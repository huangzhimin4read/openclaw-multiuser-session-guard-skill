# OpenClaw Multiuser Session Guard Skill (English)

## 1. Why this skill exists

When one OpenClaw bot serves multiple users/chats concurrently, unstable session routing can cause:

- context bleed between users,
- wrong context selection for a chat window,
- restart loops when an invalid `session.dmScope` is written.

This skill addresses all three by enforcing a valid routing policy and making it persistent.

## 2. What it does

### 2.1 Human policy -> valid dmScope mapping

- `per-window` -> `per-channel-peer` (recommended)
- `shared` -> `main`
- `per-peer` -> `per-peer`
- `per-account-channel-peer` -> `per-account-channel-peer`

### 2.2 Startup-time auto-fix

The skill installs a systemd user drop-in that runs before `openclaw-gateway` starts.
It validates and auto-corrects `session.dmScope` so invalid values do not crash routing.

## 3. Installation workflow

Assume the skill is installed at:
`~/.openclaw/skills/openclaw-multiuser-session-guard-skill`

### 3.1 Enforce once

```bash
python3 scripts/dmscope_guard.py ensure --mode per-window
```

### 3.2 Install persistent guard

```bash
python3 scripts/dmscope_guard.py install-systemd --mode per-window --cleanup-legacy
```

This writes a drop-in (default: `20-skill-multiuser-session-guard.conf`) and wires `ExecStartPre` to the guard script.

## 4. Verification checklist

```bash
openclaw config get session.dmScope --json
openclaw gateway status --json
openclaw channels status --probe --json
```

Expected:

- target `dmScope` is active (typically `per-channel-peer`),
- gateway service is active and `rpc.ok=true`,
- channel probe is healthy.

## 5. Recommended usage patterns

### Pattern A: Parallel DM/group conversations (isolation first)

Use `--mode per-window`.

### Pattern B: Shared collaborative context

Use `--mode shared`.

### Pattern C: Recovery after accidental invalid edits

```bash
python3 scripts/dmscope_guard.py ensure --mode per-window
systemctl --user restart openclaw-gateway
```

## 6. Upgrade resilience

Because the skill lives under `~/.openclaw/skills` and the drop-in runs at startup,
policy enforcement survives routine OpenClaw upgrades.

## 7. Troubleshooting

1. Gateway unreachable:
   - check `systemctl --user status openclaw-gateway`,
   - then `openclaw gateway status --json`.
2. Skill not found:
   - ensure folder name and `SKILL.md` frontmatter `name` match,
   - ensure `SKILL.md` is valid.
3. Policy not applied:
   - verify drop-in path and `ExecStartPre` target,
   - run `systemctl --user daemon-reload` and restart gateway.

## 8. Security notes

- Prefer explicit `plugins.allow` trust pinning.
- Do not store secrets/tokens in docs or repository files.
- Back up `~/.openclaw/openclaw.json` before policy changes.
