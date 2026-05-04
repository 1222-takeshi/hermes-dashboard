PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup dev-setup test config config-full up up-lite up-full down logs doctor backup tailscale-serve tailscale-serve-uptime

setup:
	bash scripts/init-env.sh
	mkdir -p data/hermes backups
	test -f data/hermes/config.yaml || cp config/hermes/config.yaml.example data/hermes/config.yaml

dev-setup:
	test -x $(PY) || python3 -m venv .venv
	$(PIP) install -r requirements-dev.txt

test: dev-setup
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PY) -m pytest -q

config: setup
	docker compose --profile monitoring-lite config >/dev/null

config-full: setup
	. ./.env; test -n "$${GRAFANA_ROOT_URL}" && test -n "$${GRAFANA_ADMIN_PASSWORD}" && docker compose --profile monitoring-lite --profile monitoring-full config >/dev/null

up:
	docker compose up -d hermes-gateway hermes-dashboard

up-lite:
	docker compose --profile monitoring-lite up -d

up-full:
	docker compose --profile monitoring-lite --profile monitoring-full up -d

down:
	docker compose --profile monitoring-lite --profile monitoring-full down

logs:
	docker compose logs -f --tail=100 hermes-gateway hermes-dashboard monitor-proxy

doctor:
	docker compose run --rm hermes-gateway doctor

backup:
	mkdir -p backups
	docker compose run --rm hermes-gateway backup --quick --output /workspace/backups/hermes-quick-backup.zip

tailscale-serve:
	. ./.env 2>/dev/null || true; tailscale serve http://127.0.0.1:$${MONITOR_PROXY_PORT:-8080}

tailscale-serve-uptime:
	. ./.env 2>/dev/null || true; tailscale serve http://127.0.0.1:$${UPTIME_KUMA_PORT:-3001}
