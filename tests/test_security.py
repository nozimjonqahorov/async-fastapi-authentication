from user.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_creates_hash():
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert hashed.startswith("$2")


def test_verify_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "1"})
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_and_decode_refresh_token():
    token = create_refresh_token({"sub": "42"})
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_decode_invalid_token_returns_none():
    assert decode_token("invalid.token.here") is None
