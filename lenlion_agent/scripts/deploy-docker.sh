#!/usr/bin/env bash
# DEPRECATED: Lenlion Agent no longer supports Docker deployment.
# See DEPLOYMENT.md for local install + cloud DATABASE_URL.
set -euo pipefail

cat <<'EOF'
Lenlion Agent Docker deployment has been removed.

Run the agent locally and point DATABASE_URL at cloud Postgres:

  cd lenlion_agent
  pip install -e ".[cli,web,mcp,cron,postgres]"
  # set DATABASE_URL in ~/.hermes/.env
  lenlion setup
  lenlion dashboard

Full guide: lenlion_agent/DEPLOYMENT.md
Platform stack: lenlion_platform/docker-compose.yml
EOF
exit 1
