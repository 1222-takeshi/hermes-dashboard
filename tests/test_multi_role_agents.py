from pathlib import Path
import shutil
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROUTE_PLACEHOLDERS = {
    "REPLACE_WITH_PMO_CHANNEL_ID": "PMO",
    "REPLACE_WITH_DEV_A_CHANNEL_ID": "Development A PM",
    "REPLACE_WITH_DEV_B_CHANNEL_ID": "Development B PM",
}


def test_single_gateway_uses_one_discord_bot_with_channel_routes():
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose["services"]

    assert "hermes-gateway" in services
    assert "hermes-pmo-gateway" not in services
    assert "hermes-dev-a-pm-gateway" not in services
    assert "hermes-dev-b-pm-gateway" not in services
    assert services["hermes-gateway"]["container_name"] == "hermes-gateway"
    assert services["hermes-gateway"]["command"] == ["gateway", "run"]


def test_config_example_defines_channel_prompts_and_skill_bindings():
    config = yaml.safe_load((ROOT / "config" / "hermes" / "config.yaml.example").read_text())
    discord = config["discord"]

    assert discord["allowed_channels"] == "${DISCORD_ALLOWED_CHANNELS}"
    assert set(discord["channel_prompts"]) == set(ROUTE_PLACEHOLDERS)

    for channel_id, role_label in ROUTE_PLACEHOLDERS.items():
        prompt = discord["channel_prompts"][channel_id]
        assert role_label in prompt
        assert "Issue" in prompt
        assert "TDD" in prompt

    bindings = {entry["id"]: entry["skills"] for entry in discord["channel_skill_bindings"]}
    assert set(bindings) == set(ROUTE_PLACEHOLDERS)
    assert "github-issues" in bindings["REPLACE_WITH_PMO_CHANNEL_ID"]
    assert "github-pr-workflow" in bindings["REPLACE_WITH_DEV_A_CHANNEL_ID"]
    assert "test-driven-development" in bindings["REPLACE_WITH_DEV_B_CHANNEL_ID"]


def test_env_example_documents_single_bot_channel_allowlist():
    env_example = (ROOT / ".env.example").read_text()

    assert "DISCORD_BOT_TOKEN=" in env_example
    assert "DISCORD_ALLOWED_USERS=" in env_example
    assert "DISCORD_ALLOWED_CHANNELS=" in env_example
    assert "DISCORD_HOME_CHANNEL=" in env_example


def test_channel_routing_preflight_rejects_placeholders(tmp_path):
    shutil.copy2(ROOT / "scripts" / "check-channel-routing.py", tmp_path / "check-channel-routing.py")

    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=test-token",
                "DISCORD_ALLOWED_USERS=123",
                "DISCORD_ALLOWED_CHANNELS=111,222,333",
                "",
            ]
        )
    )
    config_dir = tmp_path / "data" / "hermes"
    config_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "config" / "hermes" / "config.yaml.example", config_dir / "config.yaml")

    result = subprocess.run(
        [sys.executable, "check-channel-routing.py"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "replace channel route placeholders" in result.stderr


def test_channel_routing_preflight_rejects_wildcard_allowed_channels(tmp_path):
    shutil.copy2(ROOT / "scripts" / "check-channel-routing.py", tmp_path / "check-channel-routing.py")

    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=test-token",
                "DISCORD_ALLOWED_USERS=123",
                "DISCORD_ALLOWED_CHANNELS=*",
                "",
            ]
        )
    )
    config_dir = tmp_path / "data" / "hermes"
    config_dir.mkdir(parents=True)
    config = yaml.safe_load((ROOT / "config" / "hermes" / "config.yaml.example").read_text())
    config["discord"]["channel_prompts"] = {"111": "PMO route prompt"}
    config["discord"]["channel_skill_bindings"] = [{"id": "111", "skills": ["plan"]}]
    (config_dir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "check-channel-routing.py"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "DISCORD_ALLOWED_CHANNELS must list explicit channel ids" in result.stderr


def test_channel_routing_preflight_accepts_single_bot_routes(tmp_path):
    shutil.copy2(ROOT / "scripts" / "check-channel-routing.py", tmp_path / "check-channel-routing.py")

    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=test-token",
                "DISCORD_ALLOWED_USERS=123",
                "DISCORD_ALLOWED_CHANNELS=111,222,333",
                "",
            ]
        )
    )
    config_dir = tmp_path / "data" / "hermes"
    config_dir.mkdir(parents=True)
    config = yaml.safe_load((ROOT / "config" / "hermes" / "config.yaml.example").read_text())
    discord = config["discord"]
    discord["channel_prompts"] = {
        "111": "PMO route prompt",
        "222": "Development A PM route prompt",
        "333": "Development B PM route prompt",
    }
    discord["channel_skill_bindings"] = [
        {"id": "111", "skills": ["plan", "github-issues"]},
        {"id": "222", "skills": ["plan", "github-pr-workflow"]},
        {"id": "333", "skills": ["test-driven-development", "github-pr-workflow"]},
    ]
    (config_dir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "check-channel-routing.py"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "channel routing config looks valid" in result.stdout


def test_multi_role_docs_describe_single_bot_virtual_agents():
    doc = (ROOT / "docs" / "multi-role-agents.md").read_text().lower()

    for phrase in [
        "single discord bot",
        "channel_prompts",
        "channel_skill_bindings",
        "virtual agent",
        "pmo",
        "development a pm",
        "development b pm",
        "forum thread",
        "bot token",
        "tailscale",
    ]:
        assert phrase in doc


def test_makefile_exposes_channel_route_validation():
    makefile = (ROOT / "Makefile").read_text()

    assert "check-channel-routing:" in makefile
    assert "scripts/check-channel-routing.py" in makefile
