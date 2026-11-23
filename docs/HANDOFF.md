# Handoff

Read this first in a new session, then do the task you were given. Keep it to one page. Update it at the end of every
finished task (state, next steps, pitfalls). Use roles, never people's names.

Last updated: 2026-11-23

## Current state

- Code: GitHub `main` is current. Local, GitHub, and the server match.
- Live at **https://deals.dbgi.ph** (also `http://187.127.124.78:8081`), Hostinger KVM4 VPS, folder `/opt/dbgi-portal`,
  compose file `docker-compose.test-server.yml`. This server is the permanent home.
- Still **test mode** (`DJANGO_DEBUG=true`: one-click login list, practice data) while employees test.
- Real email is on (SMTP, sent as support@dbgi.ph). Practice sends real emails to accounts with real addresses.
- Backups: daily 05:30 Manila to `/opt/dbgi-portal/backups` (14 days) and, encrypted, to the backup Google Drive
  (30 days). See `docs/TECHNICAL_INFRASTRUCTURE_PROPOSAL_2026-10-21.md`.
- One snapshot on the server: **"Before practice"**. Restore it before each practice session.
- Tests: backend 187 (4 skipped), Playwright 38, Vitest 12. Ruff, tsc, lint clean.

## Next

1. Employee practice sessions, then fix what confuses people.
2. Go-live when testing ends: debug off, remove `DJANGO_ALLOW_HTTP_COOKIES`, new secret key and passwords, clean data,
   decide on a separate practice copy. The server is shared and its root user can read everything; DBGI must accept
   that before real data goes in.
3. DBGI's real program rules may change defaults (5% admin discount limit, 1,000,000 unlisted minimum). Most are
   settings in Django Admin, not code.

## How to work here

- Rules: `AGENTS.md`, then the standards files it lists. No en or em dashes anywhere. Dates `YYYY-MM-DD`.
- Run locally: `run-backend.cmd` and `run-frontend.cmd`, each in its own terminal. Do not run `start-backend.ps1`
  (real SMTP).
- Commit and deploy only when the user asks. Commit on a branch, fast-forward `main`, push, delete the branch.
- Deploy: build `frontend` locally, upload `registrations config templates devtools deploy frontend/dist
  frontend/nginx.conf`, `docker build -t dbgi-portal-web .`, `docker compose -f docker-compose.test-server.yml up -d`,
  `migrate`, then **restart nginx** (after replacing `frontend/dist` the site returns 403 until nginx restarts).

## Pitfalls

- Vitest: run from `D:\` (uppercase) in PowerShell. A lowercase `d:` working folder breaks it.
- The server also runs another person's services (Pterodactyl, game servers, Traefik). Touch only `/opt/dbgi-portal`
  and the portal's containers. Never edit Traefik's config.
- If the HTTPS certificate fails, stop the portal's nginx for about 12 seconds and start it again; Traefik retries.
- Server clock is UTC; the portal uses Asia/Manila.
- Never commit colleagues' names, filled forms, passwords, or keys.
