#!/usr/bin/env python3
"""OpenClaw session.dmScope guard helper.

Supports two main actions:
1) Ensure dmScope is a valid desired value.
2) Install a systemd user drop-in that enforces dmScope before gateway start.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

ALLOWED_SCOPES = {
    "main",
    "per-peer",
    "per-channel-peer",
    "per-account-channel-peer",
}

MODE_TO_SCOPE = {
    "per-window": "per-channel-peer",
    "shared": "main",
    "per-peer": "per-peer",
    "per-account-channel-peer": "per-account-channel-peer",
}


def default_config_path() -> Path:
    override = os.environ.get("OPENCLAW_CONFIG_FILE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".openclaw" / "openclaw.json"


def read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"config file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json in {path}: {exc}")

    if not isinstance(data, dict):
        raise SystemExit(f"config root must be an object: {path}")
    return data


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=True)
            tmp.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def resolve_scope(mode: str | None, scope: str | None) -> str:
    if scope:
        if scope not in ALLOWED_SCOPES:
            allowed = ", ".join(sorted(ALLOWED_SCOPES))
            raise SystemExit(f"invalid --scope={scope!r}, allowed: {allowed}")
        return scope

    effective_mode = mode or "per-window"
    if effective_mode not in MODE_TO_SCOPE:
        allowed = ", ".join(sorted(MODE_TO_SCOPE))
        raise SystemExit(f"invalid --mode={effective_mode!r}, allowed: {allowed}")
    return MODE_TO_SCOPE[effective_mode]


def ensure_scope(config_path: Path, target_scope: str, check_only: bool) -> int:
    data = read_json(config_path)
    session = data.get("session")
    if not isinstance(session, dict):
        session = {}
        data["session"] = session

    current = session.get("dmScope")
    need_change = (current not in ALLOWED_SCOPES) or (current != target_scope)

    if not need_change:
        print(f"OK: session.dmScope already {current}")
        return 0

    reason = "invalid" if current not in ALLOWED_SCOPES else "mismatch"
    if check_only:
        print(
            f"NEEDS_CHANGE: session.dmScope={current!r} ({reason}), target={target_scope!r}"
        )
        return 2

    session["dmScope"] = target_scope
    write_json_atomic(config_path, data)
    print(
        f"UPDATED: session.dmScope {current!r} -> {target_scope!r} "
        f"(reason={reason}, file={config_path})"
    )
    return 0


def systemctl_user(*args: str) -> None:
    cmd = ["systemctl", "--user", *args]
    subprocess.run(cmd, check=True)


def install_dropin(
    target_scope: str,
    service: str,
    dropin_name: str,
    restart: bool,
    cleanup_legacy: bool,
) -> int:
    skill_script = Path(__file__).resolve()
    dropin_dir = Path.home() / ".config" / "systemd" / "user" / f"{service}.d"
    dropin_dir.mkdir(parents=True, exist_ok=True)
    dropin_path = dropin_dir / dropin_name

    # Reset ExecStartPre list then add one deterministic guard invocation.
    content = (
        "[Service]\n"
        "ExecStartPre=\n"
        f"ExecStartPre=/usr/bin/env python3 {skill_script} ensure --scope {target_scope}\n"
    )
    dropin_path.write_text(content, encoding="utf-8")
    print(f"WROTE: {dropin_path}")

    if cleanup_legacy:
        legacy_dropin = dropin_dir / "10-ensure-dmscope.conf"
        legacy_script = Path.home() / ".local" / "bin" / "openclaw-ensure-dmscope.py"
        for legacy in (legacy_dropin, legacy_script):
            if legacy.exists():
                legacy.unlink()
                print(f"REMOVED_LEGACY: {legacy}")

    try:
        systemctl_user("daemon-reload")
        if restart:
            systemctl_user("restart", service)
        systemctl_user("is-active", service)
    except subprocess.CalledProcessError as exc:
        print(f"systemd command failed: {exc}", file=sys.stderr)
        return 1

    print(f"INSTALLED: {service} now guarded with dmScope={target_scope}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenClaw dmScope guard")
    sub = p.add_subparsers(dest="command", required=True)

    ensure = sub.add_parser("ensure", help="Ensure dmScope value in openclaw.json")
    ensure.add_argument("--config", type=Path, default=default_config_path())
    ensure.add_argument("--mode", choices=sorted(MODE_TO_SCOPE), default="per-window")
    ensure.add_argument("--scope", choices=sorted(ALLOWED_SCOPES))
    ensure.add_argument("--check-only", action="store_true")

    install = sub.add_parser(
        "install-systemd",
        help="Install systemd user drop-in to enforce dmScope at gateway startup",
    )
    install.add_argument("--mode", choices=sorted(MODE_TO_SCOPE), default="per-window")
    install.add_argument("--scope", choices=sorted(ALLOWED_SCOPES))
    install.add_argument("--service", default="openclaw-gateway.service")
    install.add_argument("--dropin-name", default="20-skill-dmscope-guard.conf")
    install.add_argument("--no-restart", action="store_true")
    install.add_argument("--cleanup-legacy", action="store_true")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ensure":
        target_scope = resolve_scope(args.mode, args.scope)
        config_path: Path = args.config.expanduser()
        return ensure_scope(config_path, target_scope, args.check_only)

    if args.command == "install-systemd":
        target_scope = resolve_scope(args.mode, args.scope)
        return install_dropin(
            target_scope=target_scope,
            service=args.service,
            dropin_name=args.dropin_name,
            restart=not args.no_restart,
            cleanup_legacy=args.cleanup_legacy,
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
