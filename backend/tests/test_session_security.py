from app.core.session_security import generate_session_token, hash_token


def test_session_tokens_are_unique():
    first = generate_session_token()
    second = generate_session_token()

    assert first != second


def test_token_hash_is_deterministic():
    token = generate_session_token()

    assert hash_token(token) == hash_token(token)


def test_token_hash_does_not_expose_token():
    token = generate_session_token()
    hashed = hash_token(token)

    assert hashed != token
    assert len(hashed) == 64