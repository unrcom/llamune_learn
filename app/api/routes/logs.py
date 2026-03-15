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


@router.get("", status_code=200)
def get_logs(
    poc_id: int = Query(...),
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """訓練データ候補のログ一覧を取得（training_role設定済みのもの）"""
    if dataset_id:
        sql = text("""
            SELECT
                cl.id,
                cl.question,
                cl.answer,
                cl.expected_answer,
                cl.training_role,
                cl.evaluation,
                cl.timestamp
            FROM conversation_logs cl
            JOIN sessions s ON cl.session_id = s.id
            JOIN conversation_log_datasets cld ON cl.id = cld.log_id
            WHERE s.poc_id = :poc_id
              AND cld.dataset_id = :dataset_id
              AND cl.training_role IS NOT NULL
            ORDER BY cl.id DESC
        """)
        rows = db.execute(sql, {"poc_id": poc_id, "dataset_id": dataset_id}).fetchall()
    else:
        sql = text("""
            SELECT
                cl.id,
                cl.question,
                cl.answer,
                cl.expected_answer,
                cl.training_role,
                cl.evaluation,
                cl.timestamp
            FROM conversation_logs cl
            JOIN sessions s ON cl.session_id = s.id
            WHERE s.poc_id = :poc_id
              AND cl.training_role IS NOT NULL
            ORDER BY cl.id DESC
        """)
        rows = db.execute(sql, {"poc_id": poc_id}).fetchall()

    return [
        {
            "id": row.id,
            "question": row.question,
            "answer": row.answer,
            "expected_answer": row.expected_answer,
            "training_role": row.training_role,
            "training_role_label": TRAINING_ROLE_LABELS.get(row.training_role, "不明"),
            "evaluation": row.evaluation,
            "timestamp": row.timestamp,
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
