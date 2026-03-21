cat > ~/dev/llamune_learn/README.md << 'EOF'
# llamune_learn

llamune プロジェクトのファインチューニング用アプリケーションです。llamune_poc の評価結果をもとに訓練データを管理し、Apple MLX を使ってローカル環境でファインチューニングを実行します。

## 主な機能

- **ジョブ管理** — 訓練ジョブの作成・実行・結果確認
- **訓練データ選択** — poc の評価済みログからデータセット・作成者・訓練状況でフィルタリング
- **2つの訓練モード** — バッチモード（全件まとめて学習）/ 1件ずつモード（loss閾値で管理）
- **アダプター管理** — LoRAアダプターの系譜（parent_model_id）追跡
- **リアルタイム状態表示** — WebSocket で訓練中ステータスをナビバーに表示
- **valid データ対応** — train/valid の役割分離（role カラム）

## 技術スタック

| コンポーネント | 技術 |
|---|---|
| フロントエンド | React + Vite + TypeScript + Tailwind CSS + shadcn/ui + Tanstack Query |
| バックエンド | Python 3.11 / FastAPI |
| ファインチューニング | Apple MLX / LoRA（mlx_lm.lora） |
| データベース | PostgreSQL 16（llamune_poc と同一DB・learnスキーマ） |
| 認証 | JWT（Bearer トークン、poc と共用）|
| マイグレーション | Alembic（learnスキーマ専用バージョン管理） |
| プロセス管理 | pm2 |

## 動作環境

- Apple Silicon Mac（M4 Mac mini 64GB で開発・検証済み）
- Python 3.11
- PostgreSQL 16
- Node.js 18+

## DBスキーマ構成

llamune_poc と同一DBを使用し、`learn` スキーマにテーブルを作成します。

| スキーマ | テーブル | 説明 |
|---------|---------|------|
| public | conversation_logs | poc の評価済みログ（参照のみ） |
| public | models | ベースモデル・訓練済みモデル管理 |
| learn | training_jobs | 訓練ジョブ管理 |
| learn | training_data | ジョブとログの紐付け（train/valid） |
| learn | valid_data | 独立したvalidデータ |

## セットアップ

### 1. 仮想環境と依存ライブラリ
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定
```bash
cp .env.example .env
```

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL 接続 URL（llamune_poc と同じ DB） |
| `MONKEY_URL` | llamune_monkey の URL |
| `SELF_URL` | monkey がこのインスタンスへ接続する URL |
| `INTERNAL_TOKEN` | monkey との内部通信用トークン |
| `INSTANCE_ID` | このインスタンスの識別子（例: llamune-learn-1） |
| `INSTANCE_DESCRIPTION` | このインスタンスの説明 |
| `HEARTBEAT_INTERVAL` | monkey へのハートビート間隔（秒） |
| `JWT_SECRET` | JWT 署名用シークレット（poc と同じ値） |
| `JWT_EXPIRE_MINUTES` | JWT の有効期限（分） |
| `DATA_DIR` | 訓練データJSONL の保存先（デフォルト: ~/llamune_data） |
| `MODEL_DIR` | アダプターの保存先（デフォルト: ~/llamune_models） |

### 3. マイグレーションの実行
```bash
alembic upgrade head
```

### 4. フロントエンドのセットアップ
```bash
cd web && npm install && cd ..
```

フロントエンドの環境変数:
```bash
cp web/.env.example web/.env
```

| 変数名 | 説明 |
|--------|------|
| `VITE_MONKEY_URL` | llamune_monkey の HTTP URL |
| `VITE_MONKEY_WS_URL` | llamune_monkey の WebSocket URL |

## 起動方法

### pm2 で起動（推奨）
```bash
pm2 start ecosystem.config.cjs
```

### 手動起動
```bash
# バックエンド
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8100

# フロントエンド（別ターミナル）
cd web && npm run dev
```

## 訓練モードについて

### バッチモード（training_mode=1）
- 全件まとめて `mlx_lm.lora` に投入
- `--iters` で指定した回数まで実行
- データが多い場合に適している

### 1件ずつモード（training_mode=2）
- 1件ずつ `mlx_lm.lora` を実行
- 各件の loss が `loss_threshold` を下回ったら除外
- 前回のアダプターを `--resume-adapter-file` で引き継ぎ
- データが少ない場合に適している

## アダプター管理

訓練済みモデルは `public.models` テーブルに登録されます。

| カラム | 説明 |
|--------|------|
| `model_name` | モデルの識別名 |
| `base_model` | ベースモデルのパス |
| `adapter_path` | LoRAアダプターの保存先 |
| `parent_model_id` | 親モデルのID（系譜追跡用） |

## llamune_monkey との連携
```
learn 起動      → POST /api/registry/register（allowed_apps に訓練済みモデルを登録）
定期ハートビート → PUT  /api/registry/{instance_id}/heartbeat
訓練開始        → PATCH /api/registry/{instance_id}（model_status: training）
訓練完了        → PATCH /api/registry/{instance_id}（model_status: idle）
```

## ライセンス

MIT
