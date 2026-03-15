import asyncio
import os
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import jobs, logs

MONKEY_URL = os.getenv("MONKEY_URL", "")
INSTANCE_ID = os.getenv("INSTANCE_ID", "unnamed")
INSTANCE_DESCRIPTION = os.getenv("INSTANCE_DESCRIPTION", INSTANCE_ID)
SELF_URL = os.getenv("SELF_URL", "http://localhost:8100")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))


def get_allowed_apps() -> list:
    """実行中・完了済みジョブからallowed_appsを組み立てる"""
    from app.db.database import get_db
    from app.models.base import TrainingJob
    db = next(get_db())
    try:
        jobs = db.query(TrainingJob).filter(
            TrainingJob.instance_id == INSTANCE_ID,
            TrainingJob.status.in_([2, 3]),  # 実行中・完了済み
        ).all()
        result = []
        for job in jobs:
            if job.output_model_name:
                result.append({
                    "app_name": job.output_model_name,
                    "version": job.id,
                })
        return result
    finally:
        db.close()


async def _register(client: httpx.AsyncClient) -> bool:
    try:
        allowed_apps = get_allowed_apps()
        await client.post(
            f"{MONKEY_URL}/api/registry/register",
            json={
                "instance_id": INSTANCE_ID,
                "url": SELF_URL,
                "description": INSTANCE_DESCRIPTION,
                "allowed_apps": allowed_apps,
            },
            headers={"X-Internal-Token": INTERNAL_TOKEN},
            timeout=5.0,
        )
        print(f"✅ Registered to monkey: {INSTANCE_ID} (allowed_apps: {allowed_apps})")
        return True
    except Exception as e:
        print(f"⚠️  Failed to register to monkey: {e}")
        return False


async def _heartbeat_loop():
    await asyncio.sleep(HEARTBEAT_INTERVAL)
    async with httpx.AsyncClient() as client:
        while True:
            try:
                allowed_apps = get_allowed_apps()
                res = await client.put(
                    f"{MONKEY_URL}/api/registry/{INSTANCE_ID}/heartbeat",
                    json={"allowed_apps": allowed_apps},
                    headers={"X-Internal-Token": INTERNAL_TOKEN},
                    timeout=5.0,
                )
                if res.status_code == 404:
                    print(f"⚠️  Heartbeat 404 — re-registering: {INSTANCE_ID}")
                    await _register(client)
            except Exception as e:
                print(f"⚠️  Heartbeat failed: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    heartbeat_task = None
    if MONKEY_URL:
        async with httpx.AsyncClient() as client:
            await _register(client)
        heartbeat_task = asyncio.create_task(_heartbeat_loop())

    yield

    if heartbeat_task:
        heartbeat_task.cancel()
    if MONKEY_URL:
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{MONKEY_URL}/api/registry/{INSTANCE_ID}",
                    headers={"X-Internal-Token": INTERNAL_TOKEN},
                    timeout=5.0,
                )
            print(f"🗑️  Unregistered from monkey: {INSTANCE_ID}")
        except Exception as e:
            print(f"⚠️  Failed to unregister from monkey: {e}")


app = FastAPI(title="llamune_learn API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(jobs.router)
app.include_router(logs.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
