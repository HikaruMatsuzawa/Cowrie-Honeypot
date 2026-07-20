"""Classify attacker-entered commands without executing them."""

from __future__ import annotations

from enum import StrEnum


class CommandCategory(StrEnum):
    SYSTEM_INFO = "システム情報確認"
    USER_CHECK = "ユーザー確認"
    NETWORK_CHECK = "ネットワーク確認"
    PROCESS_CHECK = "プロセス確認"
    FILE_OPERATION = "ファイル操作"
    PERMISSION_CHANGE = "権限変更"
    DOWNLOAD = "ダウンロード"
    EXECUTION = "実行"
    PERSISTENCE_ATTEMPT = "永続化試行"
    TRACE_REMOVAL = "痕跡削除"
    UNKNOWN = "不明"


_CATEGORY_PATTERNS: tuple[tuple[CommandCategory, tuple[str, ...]], ...] = (
    (CommandCategory.DOWNLOAD, ("wget", "curl", "tftp")),
    (CommandCategory.PERMISSION_CHANGE, ("chmod", "chown")),
    (CommandCategory.PERSISTENCE_ATTEMPT, ("crontab", "systemctl enable", "rc.local")),
    (CommandCategory.TRACE_REMOVAL, ("rm", "history -c")),
    (CommandCategory.SYSTEM_INFO, ("uname", "hostname", "lsb_release", "cat /etc/os-release")),
    (CommandCategory.USER_CHECK, ("whoami", "id", "w")),
    (CommandCategory.NETWORK_CHECK, ("ifconfig", "ip addr", "netstat", "ss")),
    (CommandCategory.PROCESS_CHECK, ("ps", "top")),
    (CommandCategory.FILE_OPERATION, ("cat", "ls", "cp", "mv")),
    (CommandCategory.EXECUTION, ("./", "sh", "bash")),
)


def classify_command(command: str) -> CommandCategory:
    normalized = command.strip().lower()
    if not normalized:
        return CommandCategory.UNKNOWN

    for category, patterns in _CATEGORY_PATTERNS:
        if any(_matches_pattern(normalized, pattern) for pattern in patterns):
            return category

    return CommandCategory.UNKNOWN


def _matches_pattern(command: str, pattern: str) -> bool:
    if pattern.endswith(" ") or " " in pattern or pattern == "./":
        return command.startswith(pattern)
    return command == pattern or command.startswith(f"{pattern} ")
