# 已弃用

Lenlion Agent **不再使用 Docker 容器部署**。

请改用 **[DEPLOYMENT.md](./DEPLOYMENT.md)**：本机运行 Agent，通过 `DATABASE_URL` 连接云端 Postgres（由 `lenlion_platform` 或托管数据库提供）。

Platform 控制平面仍使用 `lenlion_platform/docker-compose.yml` 部署。
