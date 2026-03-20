from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/pocs", tags=["pocs"])


@router.get("", status_code=200)
def get_pocs(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """PoC一覧を取得（ジョブ数・最新アダプター情報含む）"""
    sql = text("""
        SELECT
            p.id,
            p.name,
            p.domain,
            p.app_name,
            p.model_id,
            m.model_name,
            m.adapter_path,
            COUNT(DISTINCT tj.id) AS job_count,
            MAX(tj.finished_at) AS last_trained_at
        FROM poc p
        LEFT JOIN models m ON p.model_id = m.id
        LEFT JOIN learn.training_jobs tj ON p.id = tj.poc_id AND tj.status = 3
        GROUP BY p.id, p.name, p.domain, p.app_name, p.model_id, m.model_name, m.adapter_path
        ORDER BY p.id
    """)
    rows = db.execute(sql).fetchall()
    return [
        {
            "id": row.id,
            "name": row.name,
            "domain": row.domain,
            "app_name": row.app_name,
            "model_id": row.model_id,
            "model_name": row.model_name,
            "adapter_path": row.adapter_path,
            "job_count": row.job_count,
            "last_trained_at": row.last_trained_at,
        }
        for row in rows
    ]
