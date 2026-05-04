#!/usr/bin/env bash
set -euo pipefail
umask 077

if [ -f .env ]; then
  chmod 600 .env
  exit 0
fi

cp .env.example .env

generated_value="$(openssl rand -base64 32 | tr -d '\n')"
tmp_file="$(mktemp)"
sed "s|^GRAFANA_ADMIN_PASSWORD=.*|GRAFANA_ADMIN_PASSWORD=${generated_value}|" .env > "${tmp_file}"
mv "${tmp_file}" .env
chmod 600 .env
