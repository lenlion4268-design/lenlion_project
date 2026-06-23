#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PSQL="${PSQL:-/Library/PostgreSQL/18/bin/psql}"

if [[ ! -x "$PSQL" ]]; then
  PSQL="$(command -v psql || true)"
fi

if [[ -z "$PSQL" ]]; then
  echo "错误: 找不到 psql，请设置 PSQL 环境变量指向 psql 路径"
  exit 1
fi

if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
  echo "用法: POSTGRES_PASSWORD=你的postgres密码 $0"
  echo "  或: $0 你的postgres密码"
  exit 1
fi

if [[ $# -ge 1 ]]; then
  POSTGRES_PASSWORD="$1"
fi

export PGPASSWORD="$POSTGRES_PASSWORD"

echo ">>> 创建数据库与用户..."
"$PSQL" -U postgres -h localhost -d postgres -f "$ROOT/scripts/init-db.sql"

if ! "$PSQL" -U postgres -h localhost -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='novel_generator'" | grep -q 1; then
  CREATEDB="${CREATEDB:-/Library/PostgreSQL/18/bin/createdb}"
  if [[ ! -x "$CREATEDB" ]]; then
    CREATEDB="$(command -v createdb || true)"
  fi
  "$CREATEDB" -U postgres -h localhost -O novel novel_generator
fi

"$PSQL" -U postgres -h localhost -d postgres -c \
  "GRANT ALL PRIVILEGES ON DATABASE novel_generator TO novel;"

echo ">>> 执行 Alembic 迁移..."
cd "$ROOT/apps/api"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
else
  source .venv/bin/activate
fi

if [[ ! -f .env ]]; then
  cp "$ROOT/.env.example" .env
  echo "已创建 apps/api/.env"
fi

alembic upgrade head

echo ""
echo ">>> 完成！数据库 novel_generator 已就绪。"
echo "    启动 API: cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
