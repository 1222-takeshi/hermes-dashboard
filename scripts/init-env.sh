#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  exit 0
fi

cp .env.example .env

generated_value="$(openssl rand -base64 32 | tr -d '\n')"
tmp_file="$(mktemp)"
sed "s|^GRAFANA_ADMIN_PASSWORD=.*|GRAFANA_ADMIN_PASSWORD=${generated_value}|" .env > "${tmp_file}"
mv "${tmp_file}" .env
