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
    result = inspect_aof(BytesIO(b"*2\r\n$3\r\nSET\r\n$67108865\r\n"))
    assert result["pending"] == ["argument_byte_limit"] and result["completed_commands"] == 0


def test_large_retained_arguments_are_drained_without_materializing_values():
    import tracemalloc

    from apps.safety.redis_retained_history import READ_CHUNK_BYTES

    class ObservedStream(BytesIO):
        largest_read = 0

        def read(self, size=-1):
            self.largest_read = max(self.largest_read, size)
            return super().read(size)

    source = ObservedStream(command(b"SET", b"private-key", b"x" * (4 * 1024 * 1024)))
    tracemalloc.start()
    try:
        result = inspect_aof(source)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert not result["pending"] and result["completed_commands"] == 1
    assert source.largest_read <= READ_CHUNK_BYTES
    assert peak < 1024 * 1024


def test_short_reads_and_missing_crlf_are_handled_safely():
    class ShortRead(BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 3))

    source = command(b"HSET", b"private-key", b"field", b"private-value")
    assert inspect_aof(ShortRead(source))["completed_commands"] == 1
    assert inspect_aof(BytesIO(source[:-2] + b"xx"))["pending"] == ["incomplete_argument"]
