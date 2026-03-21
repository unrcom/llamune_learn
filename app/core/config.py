"""
起動時引数からインスタンス情報を取得し、DBで解決する
"""
import os
from dotenv import load_dotenv

load_dotenv()

def _resolve_instance(instance_id: str, self_url_override: str | None) -> dict:
    """DBからインスタンス情報を取得する"""
    import psycopg2
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT instance_id, display_name, self_url FROM instances WHERE instance_id = %s",
            (instance_id,)
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Instance not found in DB: {instance_id}")
        _, display_name, self_url = row
        return {
            "instance_id": instance_id,
            "display_name": display_name,
            "self_url": self_url_override or self_url,
        }
    finally:
        conn.close()

# 環境変数から取得
_instance_id = os.getenv("INSTANCE_ID_ARG")
_self_url_override = os.getenv("SELF_URL_ARG")

if _instance_id:
    _info = _resolve_instance(_instance_id, _self_url_override)
    INSTANCE_ID   = _info["instance_id"]
    DISPLAY_NAME  = _info["display_name"]
    SELF_URL      = _info["self_url"]
else:
    # fallback: 従来の.env（移行期間中の互換性）
    INSTANCE_ID   = os.getenv("INSTANCE_ID", "unnamed")
    DISPLAY_NAME  = os.getenv("INSTANCE_DESCRIPTION", INSTANCE_ID)
    SELF_URL      = os.getenv("SELF_URL", "http://localhost:8100")
