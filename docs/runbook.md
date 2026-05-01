# Hermes Dashboard Runbook

This runbook keeps Hermes Agent usable as a Docker-based development and operations hub from a workstation, mini PC, or 64-bit Raspberry Pi-class host.

## Development Policy

- Issue-first: create a GitHub Issue before starting every development task. The Issue must include the goal, acceptance criteria, test plan, and operational risk.
- TDD: write the smallest failing test first, implement the smallest change that passes, then refactor.
- PR flow: create a branch or repo-local worktree from `main`, link the PR to the Issue, and keep the PR small enough to review.
- Secrets: never commit `.env`, `data/`, `backups/`, logs, tokens, or Hermes runtime state.

## Agent Team

- Orchestrator: owns decomposition, priority, final integration, and PR readiness.
- Requirements agent: turns each Issue into acceptance criteria and test cases.
- Explorer agents: inspect Hermes, Docker, Discord, Tailscale, and monitoring behavior before changes.
- Worker agents: implement isolated slices such as Compose, monitoring, docs, and dashboard UI.
- Reviewer agent: checks correctness, security, TDD evidence, Raspberry Pi / mini PC assumptions, and rollback notes.

## First Setup

```bash
make setup
```

Edit `.env` and set:

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `OLLAMA_BASE_URL`
- `HERMES_MODEL`

`make setup` generates a random `GRAFANA_ADMIN_PASSWORD` when `.env` does not exist. Keep it secret and rotate it before sharing the host with more tailnet users.

If Hermes data already exists, keep `data/hermes/config.yaml` as the source of truth for local runtime configuration. The tracked `config/hermes/config.yaml.example` is only a starting template.

## Docker Operation

Start only Hermes:

```bash
docker compose up -d hermes-gateway hermes-dashboard
```

Start the lightweight monitoring stack:

```bash
docker compose --profile monitoring-lite up -d
```

Start full metrics on mini PC-class hardware:

```bash
GRAFANA_ROOT_URL=https://<your-tailscale-serve-name>/grafana/
docker compose --profile monitoring-lite --profile monitoring-full up -d
```

Set `GRAFANA_ROOT_URL` in `.env` to the exact Tailscale Serve HTTPS URL ending in `/grafana/`. Do not use only the bare host name, because Grafana generates absolute redirects and asset URLs from this value.

Use `monitoring-full` sparingly on Raspberry Pi. Keep `PROMETHEUS_RETENTION=1d` or `3d` if disk or memory pressure is visible.

## Monitoring

The default monitoring surface is intentionally lightweight:

- Uptime Kuma checks Hermes dashboard, Hermes gateway, Ollama, and the monitor proxy.
- Dozzle shows Docker logs without SSHing into the host.
- Caddy provides one localhost entrypoint for Tailscale Serve.
- Hermes logs remain available with `docker compose logs` and `hermes logs`.

Recommended Uptime Kuma monitors:

- HTTP: `http://127.0.0.1:9119` for Hermes dashboard.
- HTTP: `http://127.0.0.1:8080/healthz` for the monitor proxy.
- HTTP: `http://127.0.0.1:11436/api/version` for Ollama on the same host.
- Docker container: `hermes-gateway`, `hermes-dashboard`, `hermes-monitor-proxy`.

Configure Uptime Kuma notifications to the Discord `ai-agent-alerts` channel using a Discord webhook.

Useful checks:

```bash
docker compose ps
docker compose logs --tail=100 hermes-gateway
docker compose logs --tail=100 hermes-dashboard
docker compose logs --tail=100 monitor-proxy
docker compose run --rm hermes-gateway doctor
docker compose run --rm hermes-gateway logs errors -n 100
```

## Tailscale Serve

Expose monitoring only through the tailnet. Do not publish these ports to the public internet.

Tailscale is the network boundary, not a replacement for least-privilege access. Restrict this host with a tailnet ACL so only your admin user or admin group can reach the Serve endpoint.

1. Install and authenticate Tailscale on the host.
2. Start the monitor proxy locally.
3. Serve the localhost proxy into the tailnet:

```bash
make tailscale-serve
```

`make tailscale-serve` reads `MONITOR_PROXY_PORT` from `.env`, so it follows custom local port assignments.

Then open the Tailscale-provided HTTPS URL and use:

- `/` or `/hermes` for Hermes dashboard.
- `/uptime` for Uptime Kuma.
- `/logs` for Dozzle.
- `/grafana` for Grafana when `monitoring-full` is enabled.
- `/prometheus` for Prometheus when `monitoring-full` is enabled.

If a third-party UI has trouble behind a path prefix, temporarily point Tailscale Serve at that localhost port directly, for example `tailscale serve http://127.0.0.1:3001` for Uptime Kuma.

Keep Tailscale Funnel disabled. If remote shell access is needed, use Tailscale SSH separately and restrict it with tailnet ACLs.

Minimum tailnet ACL intent:

- Only the owner/admin group can reach the `hermes-dashboard` host.
- Other tailnet users cannot reach `:8080`, `:9119`, `:3001`, `:9999`, `:3000`, or `:9090`.
- SSH access, if enabled, is separate from monitoring UI access.

## Raspberry Pi / Mini PC Notes

- Use a 64-bit OS on Raspberry Pi. The pinned Hermes and cAdvisor images support `linux/amd64` and `linux/arm64`, not 32-bit `linux/arm/v7`.
- Prefer Hermes gateway, Hermes dashboard, Uptime Kuma, Dozzle, and Caddy on Raspberry Pi.
- Run the LLM on a stronger host if the Raspberry Pi cannot serve the model locally.
- Point `OLLAMA_BASE_URL` to a LAN or tailnet Ollama endpoint when the LLM is remote.
- Use mini PC hardware for `monitoring-full`, especially cAdvisor, Prometheus, and Grafana.
- Pin image versions before long-running unattended operation; the initial Hermes image defaults to `latest` for compatibility with the current upstream release.

## Backup

Create a quick Hermes state backup:

```bash
docker compose run --rm hermes-gateway backup --quick --output /workspace/backups/hermes-quick-backup.zip
```

Copy `backups/` off the host periodically. It is intentionally ignored by git.

## Failure Handling

1. Check `docker compose ps`.
2. Check Uptime Kuma for the failing endpoint.
3. Inspect Dozzle or `docker compose logs`.
4. Check Hermes with `hermes doctor` and `hermes logs errors`.
5. Check Ollama with `/api/version` and a small model prompt.
6. If the issue follows a PR, roll back by reverting the PR or switching the host back to the previous git revision.
