"""Saltzer & Schroeder: least privilege, fail-safe defaults, complete mediation. Validate input, parameterize
queries, secrets from env, constant-time compare, modern hash. Never trust input; fail closed."""
import hashlib
import hmac
import os


def get_user(db, user_id):
    """Fetch a user by id. Validates input and uses a parameterized query (no SQL injection)."""
    if not str(user_id).isdigit():                       # never trust input — validate before use
        raise ValueError("invalid user id")
    return db.execute("SELECT id, email FROM users WHERE id = %s", (int(user_id),)).fetchone()


def verify_session(token: str) -> bool:
    """Verify a session token in constant time. Secret comes from the environment, never the source."""
    secret = os.environ["SESSION_SECRET"].encode()       # least privilege: secret injected, not embedded
    expected = hmac.new(secret, b"session-v1", hashlib.sha256).hexdigest()
    return hmac.compare_digest(token, expected)          # constant-time → no timing side-channel; fail closed
