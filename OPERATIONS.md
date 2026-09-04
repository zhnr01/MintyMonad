# Operations Runbook

## Start

1. Copy `.env.example` to `.env` and provide runtime values.
2. Build and start with `docker compose up --build -d`.
3. Check liveness: `curl http://127.0.0.1:5050/healthz`.
4. Check readiness: `curl http://127.0.0.1:5050/readyz`.

## Stop

Use `docker compose down`. Do not use `--volumes` unless local disposable data should be deleted.

## Rollback

Redeploy the previous image tag or revert the application commit, then repeat the health and readiness checks. Do not roll back a database migration without first reviewing whether newer code has written incompatible data.

## Failure signals

- `/healthz` failing means the process is unavailable.
- `/readyz` returning `503` means the process is alive but the database is unavailable.
- Marketplace `502` responses indicate an RPC, metadata, or upstream dependency failure.

## Known production work

The current repository provides a production WSGI container, migration-on-start, health endpoints, request IDs, safe logs, and CI checks. It is still a testnet application and requires independent contract audit, rate limiting, CSRF protection for future browser state-changing backend routes, database backup policy, and deployment secrets management before handling real funds.
