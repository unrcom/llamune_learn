import os
import httpx

MONKEY_URL = os.getenv("MONKEY_URL", "")
INSTANCE_ID = os.getenv("INSTANCE_ID", "unnamed")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "")


def _patch_status(model_status: str, current_model: str | None = None):
    """monkey にステータスを通知する"""
    if not MONKEY_URL:
        return
    try:
        import httpx
        with httpx.Client() as client:
            client.patch(
                f"{MONKEY_URL}/api/registry/{INSTANCE_ID}",
                json={"model_status": model_status, "current_model": current_model},
                headers={"X-Internal-Token": INTERNAL_TOKEN},
                timeout=3.0,
            )
    except Exception as e:
        print(f"⚠️  Failed to patch status: {e}")


def set_training(job_name: str):
    _patch_status("training", job_name)


def set_idle():
    _patch_status("idle", None)
