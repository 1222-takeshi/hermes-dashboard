#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path.cwd()
ENV_PATH = ROOT / ".env"
CONFIG_PATH = ROOT / "data" / "hermes" / "config.yaml"
PLACEHOLDER_PREFIX = "REPLACE_WITH_"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        fail("Missing .env; run make setup and fill Discord settings first.")

    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> None:
    env = read_env(ENV_PATH)
    for key in ("DISCORD_BOT_TOKEN", "DISCORD_ALLOWED_USERS", "DISCORD_ALLOWED_CHANNELS"):
        if not env.get(key):
            fail(f"{key} is required for single-bot channel routing.")

    if not CONFIG_PATH.exists():
        fail("Missing data/hermes/config.yaml; run make setup first.")

    config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    discord = config.get("discord") or {}
    channel_prompts = discord.get("channel_prompts") or {}
    channel_skill_bindings = discord.get("channel_skill_bindings") or []

    if not isinstance(channel_prompts, dict) or not channel_prompts:
        fail("discord.channel_prompts must define at least one channel route.")
    if not isinstance(channel_skill_bindings, list) or not channel_skill_bindings:
        fail("discord.channel_skill_bindings must define at least one channel route.")

    prompt_ids = {str(channel_id) for channel_id in channel_prompts}
    skill_ids = [str(entry.get("id", "")) for entry in channel_skill_bindings if isinstance(entry, dict)]
    route_ids = prompt_ids | set(skill_ids)
    if any(channel_id.startswith(PLACEHOLDER_PREFIX) for channel_id in route_ids):
        fail("replace channel route placeholders in data/hermes/config.yaml before starting.")
    if len(skill_ids) != len(set(skill_ids)):
        fail("discord.channel_skill_bindings contains duplicate channel ids.")

    allowed_channels = set(split_csv(env["DISCORD_ALLOWED_CHANNELS"]))
    if "*" in allowed_channels:
        fail("DISCORD_ALLOWED_CHANNELS must list explicit channel ids for channel routing.")

    missing_prompt_routes = sorted(allowed_channels - prompt_ids)
    missing_skill_routes = sorted(allowed_channels - set(skill_ids))
    if missing_prompt_routes:
        fail(f"missing channel_prompts for allowed channels: {', '.join(missing_prompt_routes)}")
    if missing_skill_routes:
        fail(f"missing channel_skill_bindings for allowed channels: {', '.join(missing_skill_routes)}")

    print("channel routing config looks valid")


if __name__ == "__main__":
    main()
