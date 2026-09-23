import jwt
import pytest

from app.core.auth import create_session_token, decode_session_token, hash_password, verify_password
from app.core.exceptions import AuthenticationError

SECRET = "test-secret-key-with-enough-entropy-for-tests"


class TestPasswordHashing:
    def test_verify_correct_password(self):
        hashed = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct horse battery staple")
        assert verify_password("wrong password", hashed) is False

    def test_hash_is_not_the_plaintext(self):
        hashed = hash_password("hunter2")
        assert hashed != "hunter2"

    def test_same_password_hashes_differently_each_time(self):
        # bcrypt salts per-hash - two hashes of the same password must
        # never be identical (defends against rainbow-table comparison).
        assert hash_password("hunter2") != hash_password("hunter2")


class TestSessionToken:
    def test_roundtrip(self):
        token = create_session_token("alice", secret_key=SECRET, expires_in_days=7)
        assert decode_session_token(token, secret_key=SECRET) == "alice"

    def test_wrong_secret_is_rejected(self):
        token = create_session_token("alice", secret_key=SECRET, expires_in_days=7)
        with pytest.raises(AuthenticationError):
            decode_session_token(token, secret_key="a-completely-different-secret-key")

    def test_garbage_token_is_rejected(self):
        with pytest.raises(AuthenticationError):
            decode_session_token("not-a-real-token", secret_key=SECRET)

    def test_expired_token_is_rejected(self):
        # Build an already-expired token directly rather than sleeping.
        import datetime as dt

        payload = {
            "sub": "alice",
            "iat": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10),
            "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3),
        }
        expired_token = jwt.encode(payload, SECRET, algorithm="HS256")
        with pytest.raises(AuthenticationError):
            decode_session_token(expired_token, secret_key=SECRET)

    def test_tampered_token_is_rejected(self):
        token = create_session_token("alice", secret_key=SECRET, expires_in_days=7)
        tampered = token[:-4] + ("A" * 4)
        with pytest.raises(AuthenticationError):
            decode_session_token(tampered, secret_key=SECRET)
