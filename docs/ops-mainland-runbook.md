# 国内主站部署 Runbook

本轮主站目标是腾讯云轻量应用服务器 + 自定义域名 + ICP 备案 + Docker Compose + Caddy HTTPS。

## 前置项

- 域名完成实名认证，备案主体与域名实名一致。
- 腾讯云中国内地轻量应用服务器，建议 2 核 2G 起步。
- 备案完成后再把主域名解析到服务器公网 IP。
- Cloudflare Turnstile 创建 site key 与 secret key。
- GitHub 仓库配置生产 SSH secrets 后再启用自动部署。

## 首次部署

```bash
cp .env.production.example .env.production
# 编辑 .env.production
docker compose --env-file .env.production -f docker-compose.production.yml up -d --build
docker compose --env-file .env.production -f docker-compose.production.yml ps
curl -f https://$PUBLIC_DOMAIN/api/health
```

## 备份与恢复

```bash
set -a && . ./.env.production && set +a
scripts/backup_postgres.sh
scripts/restore_postgres.sh backups/scnu-thesis-YYYYmmdd-HHMMSS.dump
```

## 验收

- `https://$PUBLIC_DOMAIN/` 首页返回 200。
- `https://$PUBLIC_DOMAIN/api/health` 返回 `ok=true`。
- 匿名 `.docx` 预检与导出可用，导出链接 30 分钟后失效。
- `/#/workbench-demo` 可交互，不触发真实上传。
- `/#/workbench` 未输入访问码时不能访问真实项目 API。
