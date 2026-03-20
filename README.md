# llamune_learn

llamune プロジェクトのファインチューニング用アプリケーションです。llamune_poc の評価結果をもとに訓練データを生成し、ローカル環境でファインチューニングを実行します。

## 技術スタック

| コンポーネント | 技術 |
|---|---|
| フロントエンド | React + Vite + TypeScript + Tailwind CSS |
| バックエンド | Python 3.11 / FastAPI |
| ファインチューニング | Apple MLX / QLoRA |
| データベース | PostgreSQL 16（llamune_poc と共用） |
| 認証 | JWT（Bearer トークン） / 内部トークン（X-Internal-Token ヘッダー） |

## 動作環境

- Apple Silicon Mac（M4 Mac mini 64GB で開発・検証済み）
- Python 3.11
- PostgreSQL 16
- Node.js 18+

## セットアップ

### 1. 依存ライブラリのインストール
```bash
pip3 install -r requirements.txt --break-system-packages
```

### 2. 環境変数の設定
```bash
cp .env.example .env
```

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL 接続 URL（llamune_poc と同じ DB を使用） |
| `MONKEY_URL` | llamune_monkey の URL |
| `SELF_URL` | monkey がこのインスタンスへ接続する URL |
| `INTERNAL_TOKEN` | monkey との内部通信用トークン（monkey と合わせる） |
| `INSTANCE_ID` | このインスタンスの識別子 |
| `INSTANCE_DESCRIPTION` | このインスタンスの説明 |
| `HEARTBEAT_INTERVAL` | monkey へのハートビート間隔（秒） |
| `JWT_SECRET` | JWT 署名用シークレット |
| `JWT_EXPIRE_MINUTES` | JWT の有効期限（分） |

### 3. フロントエンドのセットアップ
```bash
cd web
npm install
cd ..
```

## 起動方法

### バックエンド起動
```bash
uvicorn app.main:app --port 8100
```

### フロントエンド起動（別ターミナル）
```bash
cd web
npm run dev
```

## ライセンス

MIT
