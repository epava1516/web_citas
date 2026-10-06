from io import BytesIO

from apps.safety.redis_retained_history import inspect_aof


def command(*arguments):
    return (
        b"*"
        + str(len(arguments)).encode()
        + b"\r\n"
        + b"".join(b"$" + str(len(a)).encode() + b"\r\n" + a + b"\r\n" for a in arguments)
    )


def test_deleted_values_remain_historical_without_parameter_disclosure():
    raw = command(b"SET", b"private-subject-key", b"deleted-personal-value") + command(
        b"DEL", b"private-subject-key"
    )
    result = inspect_aof(BytesIO(raw))
    assert result["completed_commands"] == 2 and result["command_counts"] == {"SET": 1, "DEL": 1}
    assert not result["pending"] and not result["subject_association_complete"]
    assert "private-subject-key" not in str(result) and "deleted-personal-value" not in str(result)


def test_truncated_suffix_keeps_pending_and_prior_metadata():
    result = inspect_aof(BytesIO(command(b"SELECT", b"0") + b"*3\r\n$3\r\nSET\r\n$99\r\npartial"))
    assert result["completed_commands"] == 1 and result["pending"] == ["incomplete_argument"]


def test_unknown_names_and_inline_formats_never_appear_in_metadata():
    result = inspect_aof(BytesIO(command(b"private-unknown-command", b"secret")))
    assert result["command_counts"] == {"unsupported": 1} and result["pending"]
    assert "secret" not in str(result) and "private-unknown-command" not in str(result)
    assert inspect_aof(BytesIO(b"SET unsafe inline\r\n"))["pending"] == [
        "unsupported_command_format"
    ]


def test_argument_limits_reject_before_reading_body():
    result = inspect_aof(BytesIO(b"*2\r\n$3\r\nSET\r\n$262145\r\n"))
    assert result["pending"] == ["argument_byte_limit"] and result["completed_commands"] == 0
