# Hermes Dashboard

Docker-based Hermes Agent gateway, dashboard, and monitoring baseline for a workstation, mini PC, or 64-bit Raspberry Pi-class host.

## What This Runs

- Hermes gateway for Discord chat operations.
- Hermes dashboard on `127.0.0.1:9119`.
- Lightweight monitoring with Uptime Kuma, Dozzle, and a Caddy monitor proxy.
- Optional full metrics with Prometheus, Grafana, node-exporter, and cAdvisor.
- Tailscale Serve access through a single localhost proxy.

## Quickstart

```bash
make setup
docker compose --profile monitoring-lite up -d
```

Edit `.env` before real use:

- `DISCORD_BOT_TOKEN`
- `DISCORD_ALLOWED_USERS`
- `DISCORD_HOME_CHANNEL`
- `OLLAMA_BASE_URL`
- `HERMES_MODEL`

## Tailscale Access

The monitoring proxy binds locally. Publish it only to your tailnet:

```bash
make tailscale-serve
```

Open the Tailscale HTTPS URL and use `/` or `/hermes` for Hermes and `/logs` for Dozzle.

Uptime Kuma does not support subdirectory hosting. To inspect its UI through Tailscale, run `make tailscale-serve-uptime` and open the Tailscale URL root for that temporary view.

For the optional Grafana profile, set `GRAFANA_ROOT_URL` in `.env` to the exact Tailscale HTTPS URL ending in `/grafana/` before running `monitoring-full`.

## Development Rules

- Create a GitHub Issue before every development task.
- Use TDD: failing test, minimal implementation, refactor.
- Use Agent team roles for non-trivial work: orchestrator, requirements, explorer, workers, reviewer.
- Keep runtime state and secrets out of git.

See [docs/runbook.md](docs/runbook.md) for operations, monitoring, Raspberry Pi / mini PC notes, and failure handling.
