import os
import json
import random
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.base import TrainingJob, TrainingData

DATA_BASE_DIR = Path(os.getenv("DATA_DIR", str(Path.home() / "llamune_data")))
MODEL_BASE_DIR = Path(os.getenv("MODEL_DIR", str(Path.home() / "llamune_models")))


def _prepare_training_data(job: TrainingJob, db: Session) -> tuple[Path, list[dict]]:
    """訓練データJSONLを生成してパスとデータリストを返す"""
    data_dir = DATA_BASE_DIR / str(job.id)
    data_dir.mkdir(parents=True, exist_ok=True)

    training_data = db.query(TrainingData).filter(
        TrainingData.job_id == job.id
    ).all()

    log_ids = [td.log_id for td in training_data]

    rows = db.execute(
        text("""
            SELECT id, question, answer, expected_answer
            FROM conversation_logs
            WHERE id = ANY(:ids)
              AND answer IS NOT NULL
        """),
        {"ids": log_ids}
    ).fetchall()

    records = []
    for row in rows:
        answer = row.expected_answer or row.answer
        records.append({
            "log_id": row.id,
            "question": row.question,
            "answer": answer,
        })

    # バッチモード用 train.jsonl（全件）
    train_path = data_dir / "train.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for rec in records:
            entry = {
                "messages": [
                    {"role": "user", "content": rec["question"]},
                    {"role": "assistant", "content": rec["answer"]},
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return data_dir, records


def _run_mlx_lora(model_path: str, data_dir: Path, output_dir: Path, job: TrainingJob, log_path: Path, iters: int = None) -> tuple[int, float | None]:
    """mlx_lm.loraを実行してreturncode と最後のlossを返す"""
    effective_iters = iters or job.iters

    cmd = [
        "mlx_lm.lora",
        "--model", model_path,
        "--data", str(data_dir),
        "--adapter-path", str(output_dir),
        "--train",
        "--iters", str(effective_iters),
        "--batch-size", str(1),  # 常に1固定
        "--learning-rate", str(job.learning_rate),
        "--num-layers", str(job.num_layers),
        "--max-seq-length", str(job.max_seq_length),
        "--save-every", str(10),
    ]

    last_loss = None
    with open(log_path, "a") as log_file:
        result = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    # ログから最後のlossを取得
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "Train loss" in line:
                try:
                    last_loss = float(line.split("Train loss")[1].split(",")[0].strip())
                except Exception:
                    pass
                break

    return result.returncode, last_loss


def _cleanup_checkpoints(output_dir: Path):
    """チェックポイントファイルを削除してadapters.safetensorsだけ残す"""
    for f in output_dir.glob("*_adapters.safetensors"):
        f.unlink()


def _get_latest_checkpoint(output_dir: Path) -> Path | None:
    """最新のチェックポイントファイルを返す"""
    checkpoints = sorted(output_dir.glob("*_adapters.safetensors"))
    return checkpoints[-1] if checkpoints else None


def run_training(job_id: int, db_url: str):
    """訓練を実行する（training_modeに応じてバッチ/1件ずつを切り替え）"""
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
            text("SELECT model_name, base_model, adapter_path FROM models WHERE id = :id"),
            {"id": job.model_id}
        ).fetchone()
        if not model_row:
            job.status = 4
            job.error_message = "モデルが見つかりません"
            db.commit()
            return

        # ベースモデルのパスを決定
        model_path = model_row.base_model or model_row.model_name

        job.status = 2
        job.started_at = datetime.now()
        db.commit()

        data_dir = DATA_BASE_DIR / str(job_id)
        output_dir = MODEL_BASE_DIR / str(job_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = data_dir / "train.log"

        data_dir, records = _prepare_training_data(job, db)

        if job.training_mode == 1:
            # バッチモード: 全件まとめて学習
            _run_batch_mode(job, model_path, data_dir, output_dir, log_path)
        else:
            # 1件ずつモード
            _run_sequential_mode(job, model_path, records, data_dir, output_dir, log_path)

        # 訓練済みモデルをpublic.modelsに登録
        output_model_name = f"{model_path.split('/')[-1]}-job{job_id}"
        db.execute(
            text("""
                INSERT INTO models (model_name, base_model, adapter_path, description, version)
                VALUES (:model_name, :base_model, :adapter_path, :description, 1)
            """),
            {
                "model_name": output_model_name,
                "base_model": model_path,
                "adapter_path": str(output_dir),
                "description": f"llamune_learn job_id={job_id} mode={job.training_mode} による訓練済みモデル",
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


def _run_batch_mode(job: TrainingJob, model_path: str, data_dir: Path, output_dir: Path, log_path: Path):
    """バッチモード: 全件まとめて学習"""
    returncode, last_loss = _run_mlx_lora(model_path, data_dir, output_dir, job, log_path)

    if returncode != 0:
        raise Exception(f"訓練失敗 (exit code: {returncode})")

    # loss閾値チェック: 閾値未満でなければ警告ログだけ記録
    if job.loss_threshold and last_loss and last_loss >= job.loss_threshold:
        with open(log_path, "a") as f:
            f.write(f"\nWarning: 最終loss {last_loss} が閾値 {job.loss_threshold} を下回りませんでした\n")

    _cleanup_checkpoints(output_dir)


def _run_sequential_mode(job: TrainingJob, model_path: str, records: list[dict], data_dir: Path, output_dir: Path, log_path: Path):
    """1件ずつモード: 各件が閾値を下回るまでランダムに繰り返す"""
    pending = list(range(len(records)))  # 未完了のインデックス
    max_rounds = job.iters  # 最大ラウンド数
    round_num = 0

    while pending and round_num < max_rounds:
        round_num += 1
        random.shuffle(pending)

        with open(log_path, "a") as f:
            f.write(f"\n=== Round {round_num} ({len(pending)} 件残り) ===\n")

        next_pending = []
        for idx in pending:
            rec = records[idx]

            # 1件用のJSONLを作成
            single_dir = data_dir / f"single_{idx}"
            single_dir.mkdir(exist_ok=True)
            single_path = single_dir / "train.jsonl"
            with open(single_path, "w", encoding="utf-8") as f:
                entry = {
                    "messages": [
                        {"role": "user", "content": rec["question"]},
                        {"role": "assistant", "content": rec["answer"]},
                    ]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # 1イテレーション実行
            returncode, last_loss = _run_mlx_lora(
                model_path, single_dir, output_dir, job, log_path, iters=1
            )

            if returncode != 0:
                raise Exception(f"訓練失敗 (exit code: {returncode})")

            # 閾値チェック
            if job.loss_threshold and last_loss is not None:
                if last_loss < job.loss_threshold:
                    with open(log_path, "a") as f:
                        f.write(f"  ✅ log_id={rec['log_id']} loss={last_loss} < {job.loss_threshold} 完了\n")
                else:
                    next_pending.append(idx)
                    with open(log_path, "a") as f:
                        f.write(f"  🔄 log_id={rec['log_id']} loss={last_loss} >= {job.loss_threshold} 継続\n")
            else:
                next_pending.append(idx)

        pending = next_pending

    _cleanup_checkpoints(output_dir)
