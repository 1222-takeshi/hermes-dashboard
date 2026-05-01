from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_compose_defines_hermes_monitoring_and_profiles():
    compose_path = ROOT / "compose.yaml"
    compose = yaml.safe_load(compose_path.read_text())

    services = compose["services"]
    assert {"hermes-gateway", "hermes-dashboard", "uptime-kuma", "dozzle", "monitor-proxy"} <= set(services)

    assert services["hermes-gateway"]["restart"] == "unless-stopped"
    assert services["hermes-gateway"]["healthcheck"]["test"] == [
        "CMD-SHELL",
        "/opt/hermes/.venv/bin/hermes status >/tmp/hermes-status.out 2>&1",
    ]
    assert services["hermes-gateway"]["env_file"] == [".env"]
    assert "./.env:/opt/data/.env:ro" in services["hermes-gateway"]["volumes"]
    assert services["hermes-dashboard"]["command"] == [
        "dashboard",
        "--host",
        "127.0.0.1",
        "--port",
        "9119",
        "--no-open",
    ]
    assert services["hermes-dashboard"]["healthcheck"]["test"][1].startswith("python3 - <<'PY'")
    assert services["monitor-proxy"]["network_mode"] == "host"
    assert services["dozzle"]["profiles"] == ["monitoring-lite"]
    assert services["uptime-kuma"]["profiles"] == ["monitoring-lite"]


def test_compose_has_optional_full_metrics_stack():
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose["services"]

    assert services["prometheus"]["profiles"] == ["monitoring-full"]
    assert services["grafana"]["profiles"] == ["monitoring-full"]
    assert services["node-exporter"]["profiles"] == ["monitoring-full"]
    assert services["cadvisor"]["profiles"] == ["monitoring-full"]
    assert services["cadvisor"]["image"] == "ghcr.io/google/cadvisor:v0.53.0"
    assert "--web.external-url=/prometheus/" in services["prometheus"]["command"]
    assert "--web.route-prefix=/prometheus" in services["prometheus"]["command"]
    assert services["grafana"]["environment"]["GF_SECURITY_ADMIN_PASSWORD"].startswith("${GRAFANA_ADMIN_PASSWORD:?")
    assert services["grafana"]["environment"]["GF_SERVER_ROOT_URL"] == "${GRAFANA_ROOT_URL:-}"
    assert "Set GRAFANA_ROOT_URL" in services["grafana"]["command"][0]
    assert "exec /run.sh" in services["grafana"]["command"][0]


def test_env_example_documents_discord_ollama_and_tailscale_defaults():
    env_example = (ROOT / ".env.example").read_text()

    for key in [
        "DISCORD_BOT_TOKEN=",
        "DISCORD_ALLOWED_USERS=",
        "DISCORD_HOME_CHANNEL=",
        "OLLAMA_BASE_URL=http://127.0.0.1:11436",
        "HERMES_MODEL=gemma4:e4b",
        "MONITOR_PROXY_PORT=8080",
        "TAILSCALE_HOSTNAME=hermes-dashboard",
        "GRAFANA_ADMIN_PASSWORD=",
        "GRAFANA_ROOT_URL=",
    ]:
        assert key in env_example

    assert "change-me" not in env_example


def test_runtime_state_paths_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text()

    for path in [
        ".env",
        "data/",
        "backups/",
        "*.log",
    ]:
        assert path in gitignore


def test_runbook_covers_issue_first_tdd_agent_team_monitoring_and_tailscale():
    runbook = (ROOT / "docs" / "runbook.md").read_text().lower()

    for phrase in [
        "issue-first",
        "tdd",
        "agent team",
        "uptime kuma",
        "dozzle",
        "tailscale serve",
        "64-bit raspberry pi",
        "mini pc",
        "tailnet acl",
    ]:
        assert phrase in runbook


def test_make_tailscale_serve_uses_configured_monitor_port():
    makefile = (ROOT / "Makefile").read_text()

    assert "tailscale serve http://127.0.0.1:$${MONITOR_PROXY_PORT:-8080}" in makefile


def test_prometheus_self_scrape_matches_subpath_route_prefix():
    prometheus = yaml.safe_load((ROOT / "config" / "prometheus" / "prometheus.yml").read_text())
    jobs = {job["job_name"]: job for job in prometheus["scrape_configs"]}

    assert jobs["prometheus"]["metrics_path"] == "/prometheus/metrics"


def test_caddy_preserves_subpaths_for_apps_that_need_them():
    caddyfile = (ROOT / "config" / "caddy" / "Caddyfile").read_text()

    assert "handle /logs/*" in caddyfile
    assert "handle /grafana/*" in caddyfile
    assert "handle /prometheus/*" in caddyfile
    assert "handle_path /prometheus/*" not in caddyfile
