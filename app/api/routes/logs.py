from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.db.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/logs", tags=["logs"])

TRAINING_ROLE_LABELS = {
    1: "correction（修正）",
    2: "reinforcement（強化）",
    3: "graduated（修了）",
    4: "negative（否定例）",
    5: "synthetic（合成）",
    6: "boundary（境界）",
}

EVALUATION_LABELS = {
    1: "良い",
    2: "不十分",
    3: "間違い",
}


@router.get("", status_code=200)
def get_logs(
    poc_id: int = Query(...),
    dataset_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    trained: Optional[str] = Query(None),  # "all" | "trained" | "untrained"
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """訓練データ候補のログ一覧を取得（training_role設定済みのもの）"""

    conditions = [
        "s.poc_id = :poc_id",
        "cl.training_role IS NOT NULL",
    ]
    params = {"poc_id": poc_id}

    if dataset_id:
        conditions.append("cld.dataset_id = :dataset_id")
        params["dataset_id"] = dataset_id

    if user_id:
        conditions.append("u.id = :user_id")
        params["user_id"] = user_id

    if trained == "trained":
        conditions.append("td.log_id IS NOT NULL")
    elif trained == "untrained":
        conditions.append("td.log_id IS NULL")

    dataset_join = "LEFT JOIN conversation_log_datasets cld ON cl.id = cld.log_id" if dataset_id else "LEFT JOIN conversation_log_datasets cld ON cl.id = cld.log_id"

    sql = text(f"""
        SELECT
            cl.id,
            cl.question,
            cl.answer,
            cl.expected_answer,
            cl.training_role,
            cl.evaluation,
            cl.timestamp,
            u.id AS user_id,
            u.username,
            td.log_id IS NOT NULL AS is_trained,
            td.final_loss,
            td.iterations,
            tj.name AS job_name,
            tj.executed_at AS trained_at,
            tj.training_mode,
            td.role AS training_data_role
        FROM conversation_logs cl
        JOIN sessions s ON cl.session_id = s.id
        LEFT JOIN users u ON s.user_id = u.id
        {dataset_join}
        LEFT JOIN learn.training_data td ON cl.id = td.log_id
        LEFT JOIN learn.training_jobs tj ON td.job_id = tj.id
        WHERE {" AND ".join(conditions)}
        ORDER BY cl.id DESC
    """)

    rows = db.execute(sql, params).fetchall()

    return [
        {
            "id": row.id,
            "question": row.question,
            "answer": row.answer,
            "expected_answer": row.expected_answer,
            "training_role": row.training_role,
            "training_role_label": TRAINING_ROLE_LABELS.get(row.training_role, "不明"),
            "evaluation": row.evaluation,
            "evaluation_label": EVALUATION_LABELS.get(row.evaluation, "未評価") if row.evaluation else "未評価",
            "timestamp": row.timestamp,
            "user_id": row.user_id,
            "username": row.username,
            "is_trained": row.is_trained,
            "final_loss": row.final_loss,
            "iterations": row.iterations,
            "job_name": row.job_name,
            "trained_at": row.trained_at,
            "training_mode": row.training_mode,
            "training_data_role": row.training_data_role,
        }
        for row in rows
    ]


@router.get("/datasets", status_code=200)
def get_datasets(
    poc_id: int = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """PoCに紐づくデータセット一覧を取得"""
    sql = text("""
        SELECT DISTINCT d.id, d.name, d.description
        FROM datasets d
        JOIN conversation_log_datasets cld ON d.id = cld.dataset_id
        JOIN conversation_logs cl ON cld.log_id = cl.id
        JOIN sessions s ON cl.session_id = s.id
        WHERE s.poc_id = :poc_id
          AND cl.training_role IS NOT NULL
        ORDER BY d.name
    """)
    rows = db.execute(sql, {"poc_id": poc_id}).fetchall()
    return [
        {"id": row.id, "name": row.name, "description": row.description}
        for row in rows
    ]
