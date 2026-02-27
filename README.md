# OpenClaw Multiuser Session Guard Skill

> Keep OpenClaw stable when multiple users and chats talk to the same bot at the same time.
>
> 让 OpenClaw 在多人、多窗口同时对话时保持会话稳定、不串上下文。

## 中文简介

这是一个用于 OpenClaw 的会话守护 Skill，核心目标是：

- 多人同时接入时，不出现会话串线；
- session 策略可控（共享 / 隔离）；
- 自动修复非法 `session.dmScope` 配置；
- OpenClaw 升级后依然持续生效（通过 systemd 启动前守护）。

详细中文文档：[`docs/intro.zh-CN.md`](docs/intro.zh-CN.md)

## English Overview

This skill helps OpenClaw handle concurrent multi-user chats safely by:

- keeping session routing deterministic,
- mapping human policy choices to valid `session.dmScope` values,
- auto-correcting invalid scope values before gateway startup,
- surviving upgrades through a systemd user drop-in.

Detailed English doc: [`docs/intro.en.md`](docs/intro.en.md)

## Quick Start

```bash
# 1) One-time enforcement (recommended policy: per-window -> per-channel-peer)
python3 scripts/dmscope_guard.py ensure --mode per-window

# 2) Install persistent startup guard
python3 scripts/dmscope_guard.py install-systemd --mode per-window --cleanup-legacy

# 3) Verify
openclaw config get session.dmScope --json
openclaw gateway status --json
openclaw channels status --probe --json
```

## Policy Modes

- `per-window` -> `per-channel-peer` (recommended)
- `shared` -> `main`
- `per-peer` -> `per-peer`
- `per-account-channel-peer` -> `per-account-channel-peer`

Invalid value to avoid: `per-channel` (may cause config validation failures/restart loops).

## Repository Structure

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── dmscope_guard.py
├── references/
│   └── session-policy.md
└── docs/
    ├── intro.zh-CN.md
    └── intro.en.md
```
