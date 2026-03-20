from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/poc/{poc_id}", status_code=200)
def get_models_by_poc(
    poc_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """PoCに紐づくモデル・アダプターの系譜を取得"""
    sql = text("""
        SELECT
            m.id,
            m.model_name,
            m.base_model,
            m.adapter_path,
            m.parent_model_id,
            m.description,
            m.created_at,
            tj.id AS job_id,
            tj.name AS job_name,
            tj.training_mode,
            tj.status AS job_status,
            tj.executed_at,
            tj.finished_at
        FROM models m
        LEFT JOIN learn.training_jobs tj ON tj.poc_id = :poc_id
            AND tj.output_model_name = m.model_name
        WHERE m.id = (SELECT model_id FROM poc WHERE id = :poc_id)
           OR m.parent_model_id IN (
               SELECT id FROM models WHERE id IN (
                   SELECT model_id FROM poc WHERE id = :poc_id
                   UNION
                   SELECT id FROM models WHERE parent_model_id IN (
                       SELECT model_id FROM poc WHERE id = :poc_id
                   )
               )
           )
        ORDER BY m.id
    """)
    rows = db.execute(sql, {"poc_id": poc_id}).fetchall()
    return [
        {
            "id": row.id,
            "model_name": row.model_name,
            "base_model": row.base_model,
            "adapter_path": row.adapter_path,
            "parent_model_id": row.parent_model_id,
            "description": row.description,
            "created_at": row.created_at,
            "job_id": row.job_id,
            "job_name": row.job_name,
            "training_mode": row.training_mode,
            "job_status": row.job_status,
            "executed_at": row.executed_at,
            "finished_at": row.finished_at,
        }
        for row in rows
    ]
