"""Bounded metadata inspection of RESP AOF; never execute or disclose arguments."""

MAX_BYTES = 64 * 1024 * 1024
MAX_ARGUMENT_BYTES = MAX_BYTES
READ_CHUNK_BYTES = 64 * 1024
MAX_ARGUMENTS = 10000
COMMANDS = frozenset(
    "SELECT SET SETEX PSETEX DEL UNLINK EXPIRE EXPIREAT PEXPIRE PEXPIREAT "
    "LPUSH RPUSH LPOP RPOP LREM LTRIM HSET HMSET HDEL SADD SREM ZADD ZREM "
    "MULTI EXEC INCR INCRBY DECR DECRBY FLUSHDB FLUSHALL XADD XDEL".split()
)
COMMAND_BYTES = frozenset(command.encode() for command in COMMANDS)


def inspect_aof(stream):
    """Counts are evidence of retained commands, not a subject-specific copy.

    Reject incomplete/oversized/unknown RESP formats without treating the
    unexamined suffix as empty. AOF arguments can contain deleted personal data.
    """
    consumed = 0
    counts = {}
    completed = 0
    pending = []

    def line():
        nonlocal consumed
        value = stream.readline(65)
        consumed += len(value)
        if consumed > MAX_BYTES or len(value) > 64 or not value.endswith(b"\r\n"):
            raise ValueError("incomplete_or_oversized_header")
        return value[:-2]

    try:
        while True:
            first = stream.read(1)
            if not first:
                break
            consumed += 1
            if first != b"*":
                raise ValueError("unsupported_command_format")
            count = int(line())
            if not 1 <= count <= MAX_ARGUMENTS:
                raise ValueError("argument_count_limit")
            command = None
            for position in range(count):
                header = line()
                if not header.startswith(b"$"):
                    raise ValueError("unsupported_argument_format")
                size = int(header[1:])
                if not 0 <= size <= MAX_ARGUMENT_BYTES:
                    raise ValueError("argument_byte_limit")
                if consumed + size + 2 > MAX_BYTES:
                    raise ValueError("aggregate_byte_limit")
                remaining = size
                command_parts = []
                while remaining:
                    raw = stream.read(min(remaining, READ_CHUNK_BYTES))
                    consumed += len(raw)
                    if not raw:
                        raise ValueError("incomplete_argument")
                    remaining -= len(raw)
                    if position == 0 and size <= 32:
                        command_parts.append(raw)
                trailer = b""
                while len(trailer) < 2:
                    raw = stream.read(2 - len(trailer))
                    consumed += len(raw)
                    if not raw:
                        raise ValueError("incomplete_argument")
                    trailer += raw
                if trailer != b"\r\n":
                    raise ValueError("incomplete_argument")
                if position == 0:
                    command = b"".join(command_parts).upper()
            label = command.decode("ascii") if command in COMMAND_BYTES else "unsupported"
            counts[label] = counts.get(label, 0) + 1
            completed += 1
            if label == "unsupported" and "unsupported_command" not in pending:
                pending.append("unsupported_command")
    except (ValueError, OverflowError) as error:
        reason = str(error)
        pending.append(
            reason
            if reason
            in {
                "incomplete_or_oversized_header",
                "unsupported_command_format",
                "argument_count_limit",
                "unsupported_argument_format",
                "argument_byte_limit",
                "aggregate_byte_limit",
                "incomplete_argument",
            }
            else "invalid_numeric_header"
        )
    return {
        "completed_commands": completed,
        "command_counts": counts,
        "examined_bytes": consumed,
        "pending": pending,
        "subject_association_complete": False,
        "original_command_times_known": False,
    }
