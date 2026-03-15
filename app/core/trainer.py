import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.base import TrainingJob, TrainingData

DATA_BASE_DIR = Path(os.getenv("DATA_DIR", str(Path.home() / "llamune_data")))
MODEL_BASE_DIR = Path(os.getenv("MODEL_DIR", str(Path.home() / "llamune_models")))


def _prepare_training_data(job: TrainingJob, db: Session) -> Path:
    """訓練データJSONLを生成してパスを返す"""
    data_dir = DATA_BASE_DIR / str(job.id)
    data_dir.mkdir(parents=True, exist_ok=True)

    training_data = db.query(TrainingData).filter(
        TrainingData.job_id == job.id
    ).all()

    log_ids = [td.log_id for td in training_data]

    rows = db.execute(
        text("""
            SELECT question, answer, expected_answer
            FROM conversation_logs
            WHERE id = ANY(:ids)
              AND answer IS NOT NULL
        """),
        {"ids": log_ids}
    ).fetchall()

    # MLX-LM の chat テンプレート形式
    train_path = data_dir / "train.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for row in rows:
            answer = row.expected_answer or row.answer
            entry = {
                "messages": [
                    {"role": "user", "content": row.question},
                    {"role": "assistant", "content": answer},
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return data_dir


def run_training(job_id: int, db_url: str):
    """訓練を実行する"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            return

        # モデルパスを取得
        model_row = db.execute(
            text("SELECT model_name, base_model FROM models WHERE id = :id"),
            {"id": job.model_id}
        ).fetchone()
        if not model_row:
            job.status = 4
            job.error_message = "モデルが見つかりません"
            db.commit()
            return

        model_path = model_row.base_model or model_row.model_name

        # 訓練データ生成
        job.status = 2
        job.started_at = datetime.now()
        db.commit()

        data_dir = _prepare_training_data(job, db)
        output_dir = MODEL_BASE_DIR / str(job_id)
        output_dir.mkdir(parents=True, exist_ok=True)

        log_path = data_dir / "train.log"

        # データ件数に合わせてbatch_sizeを自動調整
        data_count = db.query(TrainingData).filter(TrainingData.job_id == job_id).count()
        effective_batch_size = min(job.batch_size, data_count)

        cmd = [
            "mlx_lm.lora",
            "--model", model_path,
            "--data", str(data_dir),
            "--adapter-path", str(output_dir),
            "--train",
            "--iters", str(job.iters),
            "--batch-size", str(effective_batch_size),
            "--learning-rate", str(job.learning_rate),
            "--num-layers", str(job.num_layers),
            "--max-seq-length", str(job.max_seq_length),
        ]

        with open(log_path, "w") as log_file:
            result = subprocess.run(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        if result.returncode != 0:
            job.status = 4
            job.error_message = f"訓練失敗 (exit code: {result.returncode})"
            db.commit()
            return

        # 訓練済みモデルをpublic.modelsに登録
        output_model_name = f"{model_path.split('/')[-1]}-job{job_id}"
        db.execute(
            text("""
                INSERT INTO models (model_name, base_model, description, version)
                VALUES (:model_name, :base_model, :description, 1)
            """),
            {
                "model_name": output_model_name,
                "base_model": str(output_dir),
                "description": f"llamune_learn job_id={job_id} による訓練済みモデル",
            }
        )

        job.status = 3
        job.finished_at = datetime.now()
        job.output_model_name = output_model_name
        db.commit()

    except Exception as e:
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if job:
                job.status = 4
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
