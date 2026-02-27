# Session Policy Reference

## Goal

Map human conversation expectations to valid OpenClaw `session.dmScope` values.

## Recommended default

Use `per-channel-peer` for most multi-user deployments.

Why:
- Each chat window gets isolated context.
- Avoids cross-user leakage of conversational state.
- Matches user expectation: DM-A, DM-B, and group chat are separate threads.

## Valid values (OpenClaw 2026.2.26)

- `main`
- `per-peer`
- `per-channel-peer`
- `per-account-channel-peer`

## Invalid value to avoid

- `per-channel` (causes config validation failure and gateway restart loop)
