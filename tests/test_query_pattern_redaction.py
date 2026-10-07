from scripts.query_pattern_redaction import query_pattern


def test_sql_literal_and_comment_redaction_keeps_only_query_shape():
    sql = "SELECT 'person@example.invalid', E'555\\123', $$private text$$, 123.4 FROM core_user U0 WHERE id IN (%s, %s, %s) -- hidden phone\n"
    pattern = query_pattern(sql)
    for sensitive in ["person@example.invalid", "555", "private text", "123.4", "hidden phone"]:
        assert sensitive not in pattern
    assert "core_user U0" in pattern and "IN (%s[*])" in pattern
    assert query_pattern("SELECT * FROM core_user U0 WHERE id IN (%s, %s)") == query_pattern(
        "SELECT * FROM core_user U0 WHERE id IN (%s, %s, %s)"
    )


def test_comment_delimiters_inside_literal_do_not_leave_sensitive_prefix():
    pattern = query_pattern(
        "SELECT 'secret-prefix--hidden', 'another/*secret*/value', $tag$private--value$tag$ FROM core_user /* private-comment */"
    )
    for value in ["secret-prefix", "another", "private", "hidden", "value"]:
        assert value not in pattern
    assert "core_user" in pattern
