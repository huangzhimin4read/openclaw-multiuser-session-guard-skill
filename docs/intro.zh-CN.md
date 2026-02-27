# OpenClaw 多用户会话守护技能（中文）

## 1. 背景与目标

当一个 OpenClaw 机器人同时服务多个用户（多个私聊/群聊窗口）时，如果 session 路由不稳定，容易出现：

- A 用户上下文“串”到 B 用户；
- 某个窗口消息不再命中原有上下文；
- 配置被误改成非法值导致网关重启循环。

本技能专门解决以上问题：

1. 把“业务语义”映射到合法 `session.dmScope`；
2. 在网关启动前自动纠偏，防止非法配置生效；
3. 通过 systemd user drop-in 持久化，升级后仍保持策略。

## 2. 核心能力

### 2.1 策略映射

- `per-window` -> `per-channel-peer`（推荐）
  - 每个对话窗口独立 session；
  - 适合“多人并行沟通且互不干扰”的场景。
- `shared` -> `main`
  - 全部消息共享一个上下文；
  - 适合需要合并讨论上下文的场景。
- `per-peer` -> `per-peer`
  - 同一用户跨窗口共享；
  - 适合“按人聚合”的场景。
- `per-account-channel-peer` -> `per-account-channel-peer`
  - 细粒度隔离，适合多账号多连接拓扑。

### 2.2 非法值防护

当前版本中 `per-channel` 是非法值。若写入该值，可能触发配置校验失败并导致 gateway 自动重启。

本技能会在启动前校验并自动修复。

## 3. 安装与启用

> 以下示例假设技能目录已在 `~/.openclaw/skills/openclaw-multiuser-session-guard-skill`。

### 3.1 一次性修正当前配置

```bash
python3 scripts/dmscope_guard.py ensure --mode per-window
```

### 3.2 安装持久化守护

```bash
python3 scripts/dmscope_guard.py install-systemd --mode per-window --cleanup-legacy
```

此命令会：

- 写入 systemd drop-in（默认 `20-skill-multiuser-session-guard.conf`）；
- 在 `openclaw-gateway` 启动前执行 `ensure`；
- 可选清理旧历史守护脚本（`--cleanup-legacy`）。

## 4. 验证清单

```bash
# 1) 验证当前值
openclaw config get session.dmScope --json

# 2) 验证网关健康
openclaw gateway status --json

# 3) 验证渠道探针
openclaw channels status --probe --json
```

期望结果：

- `session.dmScope` 为目标值（推荐 `per-channel-peer`）；
- gateway service `active` 且 `rpc.ok=true`；
- Feishu 渠道 `configured=true`、`running=true`、`probe.ok=true`。

## 5. 常见使用场景

### 场景 A：多人并行私聊机器人

建议：`--mode per-window`。

收益：每个聊天窗口都拿到独立上下文，不会串线。

### 场景 B：需要把多人消息合并进同一思路

建议：`--mode shared`。

收益：跨聊天复用统一上下文，适合协作式对话。

### 场景 C：策略被误改导致异常

执行：

```bash
python3 scripts/dmscope_guard.py ensure --mode per-window
systemctl --user restart openclaw-gateway
```

## 6. 升级与持久化说明

只要技能安装在 `~/.openclaw/skills` 且 drop-in 仍存在，OpenClaw 升级后该策略仍会在网关启动前执行，不依赖手工重复修改。

## 7. 故障排查

1. `openclaw channels status` 显示网关不可达：
   - 先看 `systemctl --user status openclaw-gateway`；
   - 再看 `openclaw gateway status --json`。
2. `skills info` 找不到技能：
   - 检查目录名与 `SKILL.md` frontmatter `name` 是否一致；
   - 检查 `SKILL.md` 是否存在语法损坏。
3. 配置修改后不生效：
   - 确认 drop-in 是否指向当前技能路径；
   - 执行 `systemctl --user daemon-reload && systemctl --user restart openclaw-gateway`。

## 8. 安全建议

- 建议显式配置 `plugins.allow`，只信任必要插件；
- 禁止将敏感凭据写入仓库文档；
- 修改会话策略前建议先备份 `~/.openclaw/openclaw.json`。
