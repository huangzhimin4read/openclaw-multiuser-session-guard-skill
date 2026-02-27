---
name: openclaw-dmscope-guard
description: Manage OpenClaw multi-user session routing by validating and enforcing session.dmScope. Use when users ask for shared vs isolated chat context, DM/group session mapping, or dmScope persistence after upgrades.
metadata:
  openclaw:
    emoji: "🧭"
    requires:
      bins: ["python3", "systemctl"]
---

# OpenClaw DM Scope Guard

Use this skill to keep `session.dmScope` valid and stable, especially when multiple Feishu users/chats talk to one bot.

## Routing policy mapping

- `per-window` (recommended): maps to `per-channel-peer`.
  - One DM window = one session.
  - Another DM/group window = different session.
- `shared`: maps to `main`.
  - All messages share one session context.
- `per-peer`: maps to `per-peer`.
  - Same user shares context across chats.
- `per-account-channel-peer`: maps to `per-account-channel-peer`.

Never set `per-channel` (invalid in current OpenClaw schema).

## Workflow

1. Inspect current value:
   - `openclaw config get session.dmScope --json`
2. Enforce desired policy once:
   - `python3 scripts/dmscope_guard.py ensure --mode per-window`
3. Install startup guard for persistence:
   - `python3 scripts/dmscope_guard.py install-systemd --mode per-window --cleanup-legacy`
4. Verify:
   - `systemctl --user status openclaw-gateway --no-pager`
   - `openclaw config get session.dmScope --json`
   - `openclaw channels status --probe --json`

## Notes

- This skill is installed under `~/.openclaw/skills/openclaw-dmscope-guard` so OpenClaw upgrades do not overwrite it.
- The installed systemd drop-in runs before gateway start and auto-corrects `dmScope`.
- If user explicitly asks for shared context, switch to `--mode shared`.

## References

- Policy details: `references/session-policy.md`
- Automation script: `scripts/dmscope_guard.py`
