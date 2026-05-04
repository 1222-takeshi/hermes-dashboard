# Multi-Role Hermes Agents

Use a single Discord bot and one Hermes gateway, then split work by Discord channel or forum thread. This avoids creating a new bot token for every future project while still keeping PMO and project conversations separated.

## Recommended Shape

- `#pmo` -> PMO virtual agent
- `#dev-a` -> Development A PM virtual agent
- `#dev-b` -> Development B PM virtual agent
- Discord forum thread -> project-specific PM context under the parent forum route

Hermes supports this through Discord `channel_prompts` and `channel_skill_bindings` in `data/hermes/config.yaml`. A channel prompt is injected only for that channel or forum parent, and skill bindings preload the right workflow skills for that context.

## Setup

Keep one bot token in `.env`:

```bash
DISCORD_BOT_TOKEN=
DISCORD_ALLOWED_USERS=
DISCORD_ALLOWED_CHANNELS=111111111111111111,222222222222222222,333333333333333333
DISCORD_HOME_CHANNEL=111111111111111111
```

Copy the example config with `make setup`, then replace the placeholder keys in `data/hermes/config.yaml`:

```yaml
discord:
  allowed_channels: "${DISCORD_ALLOWED_CHANNELS}"
  channel_prompts:
    "111111111111111111": |
      You are the PMO virtual agent for this Discord channel.
    "222222222222222222": |
      You are the Development A PM virtual agent for this Discord channel.
  channel_skill_bindings:
    - id: "111111111111111111"
      skills: ["plan", "github-issues"]
    - id: "222222222222222222"
      skills: ["plan", "test-driven-development", "github-pr-workflow"]
```

Validate the route setup before starting Discord work:

```bash
make check-channel-routing
```

## Operating Rules

- Keep `DISCORD_ALLOWED_CHANNELS` as a whitelist, not `*`.
- Prefer one Discord channel per durable role or project stream.
- Use forum posts or threads for project subtopics so they inherit the parent channel prompt.
- Keep high-risk actions issue-backed and reviewed; the virtual agent should coordinate, not bypass the Issue -> TDD -> PR flow.
- Use Tailscale only for the monitoring dashboard; Discord remains the chat entrypoint.

## Scaling

Add a new development stream by adding one channel or forum parent ID to:

- `.env` `DISCORD_ALLOWED_CHANNELS`
- `data/hermes/config.yaml` `discord.channel_prompts`
- `data/hermes/config.yaml` `discord.channel_skill_bindings`

Do not add a new Discord bot unless you need a separate permission boundary, a separate Discord application identity, or independent gateway uptime. For unknown project counts, channel routing is the default.

For Raspberry Pi or mini PC deployments, keep this single-gateway shape and point Hermes at Ollama running on a stronger host over LAN or Tailscale when local memory is tight.
