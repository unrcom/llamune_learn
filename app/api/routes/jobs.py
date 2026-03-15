from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import os

from app.db.database import get_db
from app.models.base import TrainingJob, TrainingData
from app.core.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])

INSTANCE_ID = os.getenv("INSTANCE_ID", "unnamed")

JOB_STATUS = {1: "draft", 2: "running", 3: "done", 4: "error"}


# ---------- スキーマ ----------

class JobCreate(BaseModel):
    poc_id: int
    name: str
    log_ids: List[int]


class JobResponse(BaseModel):
    id: int
    poc_id: int
    model_id: int
    name: str
    status: int
    instance_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    output_model_name: Optional[str]
    log_count: int


# ---------- ヘルパー ----------

def _resolve_model_id(poc_id: int, db: Session) -> int:
    """PoCの訓練履歴から使用するモデルIDを決定する"""
    # 最新の完了済みジョブを探す
    latest_job = db.query(TrainingJob).filter(
        TrainingJob.poc_id == poc_id,
        TrainingJob.status == 3,
        TrainingJob.output_model_name.isnot(None),
    ).order_by(TrainingJob.id.desc()).first()

    if latest_job:
        # 訓練済みモデルのIDをpublic.modelsから取得
        result = db.execute(
            text("SELECT id FROM models WHERE model_name = :name ORDER BY version DESC LIMIT 1"),
            {"name": latest_job.output_model_name}
        ).fetchone()
        if result:
            return result[0]

    # 初回: pocのmodel_idを使用
    result = db.execute(
        text("SELECT model_id FROM poc WHERE id = :poc_id"),
        {"poc_id": poc_id}
    ).fetchone()
    if not result or not result[0]:
        raise HTTPException(status_code=400, detail="PoCにモデルが設定されていません")
    return result[0]


def _job_response(job: TrainingJob, db: Session) -> dict:
    log_count = db.query(TrainingData).filter(TrainingData.job_id == job.id).count()
    return {
        "id": job.id,
        "poc_id": job.poc_id,
        "model_id": job.model_id,
        "name": job.name,
        "status": job.status,
        "instance_id": job.instance_id,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error_message": job.error_message,
        "output_model_name": job.output_model_name,
        "log_count": log_count,
    }


# ---------- エンドポイント ----------

@router.get("/poc/{poc_id}", status_code=status.HTTP_200_OK)
def list_jobs(
    poc_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    jobs = db.query(TrainingJob).filter(
        TrainingJob.poc_id == poc_id
    ).order_by(TrainingJob.id.desc()).all()
    return [_job_response(j, db) for j in jobs]


@router.get("/{job_id}", status_code=status.HTTP_200_OK)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_response(job, db)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not job_in.log_ids:
        raise HTTPException(status_code=400, detail="ログを1件以上選択してください")

    model_id = _resolve_model_id(job_in.poc_id, db)

    job = TrainingJob(
        poc_id=job_in.poc_id,
        model_id=model_id,
        name=job_in.name,
        status=1,
        created_by=current_user["id"],
        instance_id=INSTANCE_ID,
    )
    db.add(job)
    db.flush()

    for log_id in job_in.log_ids:
        td = TrainingData(job_id=job.id, log_id=log_id)
        db.add(td)

    db.commit()
    db.refresh(job)
    return _job_response(job, db)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == 2:
        raise HTTPException(status_code=400, detail="実行中のジョブは削除できません")
    db.query(TrainingData).filter(TrainingData.job_id == job_id).delete()
    db.delete(job)
    db.commit()
