# Elite Security Engineering & Cryptography — SFT Gold

> Purpose: SFT training data for healing a competent-but-not-elite model.
> Every example here is *secure by design*, grounded in named elites, and auditable.

---

## 1. THE ELITE CANON

The following masters defined the field. Each entry lists name, era, affiliation, and the
**one signature principle** that characterises their contribution.

| # | Master | Era / Org | Signature Principle |
|---|--------|-----------|---------------------|
| 1 | **Jerome H. Saltzer & Michael D. Schroeder** | 1975, MIT | Eight design principles for protection: least privilege, fail-safe defaults, complete mediation, open design, economy of mechanism, separation of privilege, least common mechanism, psychological acceptability |
| 2 | **Auguste Kerckhoffs** | 1883, Dutch linguist | *La Cryptographie Militaire*: security must reside in the key alone, never the algorithm — "the system must not require secrecy, and it must be able to fall into the enemy's hands without disadvantage" |
| 3 | **Claude Shannon** | 1949, Bell Labs | Shannon's Maxim ("The enemy knows the system"); information-theoretic security; confusion + diffusion as the two design levers for strong ciphers |
| 4 | **Whitfield Diffie & Martin Hellman** | 1976, Stanford | *New Directions in Cryptography*: asymmetric key exchange — two parties derive a shared secret over a public channel with zero prior shared secret |
| 5 | **Ron Rivest, Adi Shamir, Leonard Adleman** | 1977, MIT | RSA: practical public-key encryption and digital signatures grounded in the hardness of integer factorisation |
| 6 | **Clifford Cocks (GCHQ, declassified 1997)** | 1973, GCHQ | Independently invented RSA three years before Rivest et al., kept secret; proof that public-key cryptography was known inside intelligence agencies before academia |
| 7 | **Dorothy Denning** | 1976, Purdue | Lattice model of secure information flow: the mathematical framework that formalises which information flows are permissible across security labels |
| 8 | **Ken Thompson** | 1984, Bell Labs | *Reflections on Trusting Trust* (Turing Award): you cannot trust code you did not compile yourself; supply-chain attacks can subvert the compiler itself, leaving source clean |
| 9 | **Aleph One (Elias Levy)** | 1996, Phrack 49 | *Smashing the Stack for Fun and Profit*: first rigorous public exposition of stack-based buffer overflows and shellcode; forced the industry to take memory safety seriously |
| 10 | **Bruce Schneier** | 1994–present | "Security is a process, not a product"; Schneier's Law: any competent cryptographer can design a cipher they cannot break — amateur attempts should never be trusted; security mindset as adversarial thinking |
| 11 | **Ross Anderson** | 1993–2023, Cambridge | *Security Engineering* (3 editions): holistic view — technical controls fail when human factors, economics, and organisational incentives are ignored; "security economics" as a discipline |
| 12 | **Steven Bellovin** | 1994, Bell Labs / Columbia | Co-authored the first firewall book (*Firewalls and Internet Security*); pioneered analysis of protocol failures and routing security; showed that most network attacks exploit protocol design flaws, not just implementation bugs |
| 13 | **Paul Kocher** | 1996–1998, Cryptography Research | Timing attacks (1996) and Differential Power Analysis (1998): *implementation* of correct algorithms can leak the key through measurable side-channels — correctness of the algorithm is necessary but not sufficient |
| 14 | **Dan Boneh** | 1996–present, Stanford | Pairing-based cryptography; rigorous Coursera/Stanford course formalising *how to use crypto correctly*; key insight: authenticated encryption is the minimum viable primitive — confidentiality without integrity is useless |
| 15 | **Matt Green** | 2000–present, Johns Hopkins | Applied cryptography engineering; named co-discoverer of TLS flaws; *A Few Thoughts on Cryptographic Engineering*: "never roll your own crypto", authenticated encryption (AEAD) as the default, and why nonce reuse is catastrophic |
| 16 | **Halvar Flake (Thomas Dullien)** | 2000–present, zynamics / Google | Pioneered patch-diffing (BinDiff) and heap exploitation; formalised binary analysis; key insight: attackers think structurally about code, defenders must too — vulnerability research is software archaeology |
| 17 | **OWASP Foundation** | 2001–present | Systematised web application security into actionable checklists (Top 10, Cheat Sheets); enforced the principle that injection, broken auth, and misconfiguration are *structural* failures, not accidents |

---

## 2. CHECKABLE ELITENESS CRITERIA

An elite-secure answer satisfies *all* applicable criteria below.
A competent-but-not-elite answer typically violates one or more.

### 2.1 Saltzer-Schroeder Principles (structural design)

| Criterion | Checkable Test |
|-----------|----------------|
| **Least Privilege** | Every process / user / API credential holds *only* the permissions it needs for that specific operation, and no more. DB accounts are read-only where writes are not needed. |
| **Fail-Safe Defaults** | Access is *denied* unless explicitly granted. Default return value is rejection, not permission. Configuration errors cause lockout, not bypass. |
| **Economy of Mechanism** | The security-critical path is as small and simple as possible. Complex logic does not live inside the trust boundary. |
| **Complete Mediation** | Every access to every resource is checked on every request. No cached authorisation is used after a privilege change without re-checking. |
| **Open Design / Kerckhoffs** | Security does not depend on keeping the algorithm or code secret. Only key/credential material must be kept secret. No "security by obscurity" load-bearing structures. |
| **Separation of Privilege** | High-value operations require multiple independent conditions (e.g., MFA, two-person approval, separate signing key). |
| **Least Common Mechanism** | Shared infrastructure across privilege levels is minimised. Separate DB connection pools per role, separate process spaces. |
| **Psychological Acceptability** | Secure path is the easy path. Developers reach for the safe API by default, not by heroic extra effort. |

### 2.2 Input Handling

| Criterion | Checkable Test |
|-----------|----------------|
| **Never Trust Input** | All external input (user, API, file, environment) is validated against an *allowlist* of expected shapes before use. |
| **Parameterise Queries** | No SQL/shell/LDAP string is built by concatenating user data. Placeholders (`%s`, `?`, named params) are always used. |
| **Validate Type, Length, Format, Range** | Input is checked for type, min/max length, format regex (allowlist), and value range before touching business logic. |
| **Encode Output Contextually** | HTML output is escaped for the rendering context (HTML entity, URL-encoding, JS-string). Never insert raw user data into HTML, JSON, or shell strings. |

### 2.3 Cryptographic Hygiene

| Criterion | Checkable Test |
|-----------|----------------|
| **Never Roll Your Own Crypto** | Only established libraries (Python `cryptography`, libsodium, BoringSSL, OpenSSL) are used. No custom cipher, custom hash, or custom RNG. |
| **Never Embed Secrets** | No API keys, passwords, private keys, or tokens appear in source code, config files committed to VCS, logs, or error messages. Secrets come from env vars (minimum) or a dedicated secrets manager (production). |
| **Authenticated Encryption (AEAD)** | Encryption always uses an AEAD mode (AES-256-GCM, ChaCha20-Poly1305). Bare encryption without integrity (AES-CBC alone, AES-ECB) is never used. |
| **Unique Nonce Per Encryption** | GCM/CTR nonces are generated fresh from a CSPRNG for every encryption call with the same key. Nonce reuse is catastrophic in GCM. |
| **Correct Password Hashing** | Passwords are hashed with Argon2id (preferred), bcrypt (≥cost 12), or scrypt — never with MD5, SHA-1, SHA-256, or raw SHA-512. |
| **Timing-Safe Comparison** | Hash digests and tokens are compared with `hmac.compare_digest` or equivalent constant-time function. Python `==` on strings leaks timing. |
| **CSPRNG for Secrets** | All tokens, nonces, IDs used in security contexts come from `secrets` module (Python) or `os.urandom`. Never from `random` module. |

### 2.4 Secrets & Session Management

| Criterion | Checkable Test |
|-----------|----------------|
| **Fail Closed** | On error, exception, or ambiguity, the system denies access. It does not default to open. |
| **Session Invalidation** | Sessions are invalidated server-side on logout. Client-side token deletion alone is insufficient. |
| **HttpOnly + Secure + SameSite on Cookies** | Session cookies set `HttpOnly` (no JS access), `Secure` (HTTPS only), `SameSite=Strict` (CSRF protection). |
| **CSRF Protection** | State-changing requests are protected by synchroniser token pattern or same-site cookies. |
| **Short-Lived Credentials** | Tokens have expiry. Refresh tokens are rotated on use. |

### 2.5 Defense in Depth

No single control is the sole line of defence. Parameterised queries *and* input validation *and*
output encoding *and* least-privilege DB account. An attacker breaching one layer gains nothing
without breaching all remaining layers.

---

## 3. FIVE COMPLETE GOLD EXAMPLES

Each example: a realistic prompt, then a complete, correct, elite-secure implementation with
inline annotations explaining *which principle* each decision enforces.

---

### Gold Example 1 — Parameterised Database Access (SQL Injection Defense)

**Prompt:**
> Write a Python function that looks up a user by username and password from a PostgreSQL database and returns their account details on successful authentication.

**Elite Implementation:**

```python
"""
Secure user lookup with parameterised queries.
Principles: Saltzer-Schroeder (fail-safe defaults, least privilege);
            OWASP A03 (injection); Kocher (timing-safe comparison);
            Boneh/Green (no raw password comparison).
"""
import hmac
import os
import psycopg2
import psycopg2.extras
import argon2  # argon2-cffi
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
from contextlib import contextmanager
from typing import Optional

# Argon2id with 2026-recommended parameters (RFC 9106 §4)
# time_cost=3, memory_cost=64MB, parallelism=4
_PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

# Principle: Never embed secrets — DSN comes from environment
_DSN = os.environ["DATABASE_URL"]  # e.g. "postgresql://user:pass@host/db"


@contextmanager
def _db_cursor(readonly: bool = True):
    """
    Principle: Least Privilege — the reporting connection is read-only.
    A separate write-privileged connection would be used only where writes
    are genuinely required (and would be a different DSN / role).
    """
    conn = psycopg2.connect(_DSN)
    try:
        if readonly:
            conn.set_session(readonly=True, autocommit=True)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if not readonly:
            conn.commit()
    except Exception:
        if not readonly:
            conn.rollback()
        raise
    finally:
        conn.close()


def lookup_user(username: str, password: str) -> Optional[dict]:
    """
    Return account dict on success, None on any failure.

    Security design:
    - Parameterised query: user data NEVER touches SQL string construction.
    - Fail-safe default: returns None on ANY failure (db error, bad creds, hash error).
    - Timing-safe: Argon2 verification is constant-time by design.
    - Least privilege: read-only DB session.
    - No secret in source: credentials come from env.
    - Defense in depth: input validation + parameterised query + PasswordHasher.
    """

    # Principle: Validate input before touching any backend (economy of mechanism)
    if not isinstance(username, str) or not (1 <= len(username) <= 64):
        return None
    if not isinstance(password, str) or not (8 <= len(password) <= 1024):
        return None
    # Allowlist: usernames are ASCII alphanumeric + underscore only
    if not username.replace("_", "").isalnum():
        return None

    try:
        with _db_cursor(readonly=True) as cur:
            # Principle: Parameterised query — %s placeholder, never f-string
            cur.execute(
                "SELECT id, username, password_hash, role, is_active "
                "FROM users WHERE username = %s",
                (username,),          # tuple of parameters, NOT string concat
            )
            row = cur.fetchone()
    except psycopg2.Error:
        # Principle: Fail closed — DB error means authentication fails,
        # never leaks partial results or exception detail to caller
        return None

    if row is None:
        # Principle: Perform a dummy verify to normalise timing
        # (prevents username-enumeration via timing oracle)
        try:
            _PH.verify(
                "$argon2id$v=19$m=65536,t=3,p=4$"
                "dG9rZW5wbGFjZWhvbGRlcg$AAAAAAAAAAAAAAAAAAAAAA",
                password,
            )
        except (VerifyMismatchError, VerificationError, InvalidHash):
            pass
        return None

    # Principle: Fail closed — inactive accounts are rejected before hash check
    if not row["is_active"]:
        return None

    try:
        # Principle: Timing-safe — Argon2 verify is constant time with respect
        # to the password bytes; do NOT use == on digest strings
        _PH.verify(row["password_hash"], password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return None

    # Principle: Rehash on algorithm upgrade (argon2-cffi handles this)
    if _PH.check_needs_rehash(row["password_hash"]):
        _schedule_rehash(row["id"], password)   # async, non-blocking

    # Return only what the caller needs — least privilege in data exposure
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
    }


def _schedule_rehash(user_id: int, password: str) -> None:
    """Fire-and-forget: update hash in background to new parameters."""
    # In production: push to a task queue (Celery, RQ) — never block the request
    new_hash = _PH.hash(password)
    try:
        with _db_cursor(readonly=False) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id),
            )
    except psycopg2.Error:
        pass  # non-fatal: stale hash is still valid


# ── NEVER DO THIS ──────────────────────────────────────────────────────────
#
# BAD: string concatenation → SQL injection
#   cur.execute(f"SELECT * FROM users WHERE username = '{username}'")
#
# BAD: weak hash
#   import hashlib; stored = hashlib.md5(password.encode()).hexdigest()
#
# BAD: == comparison on hash → timing oracle
#   if stored_hash == hashlib.sha256(password.encode()).hexdigest(): ...
#
# BAD: hardcoded DSN
#   conn = psycopg2.connect("postgresql://admin:hunter2@prod-db/app")
```

---

### Gold Example 2 — Authenticated Encryption (AES-256-GCM)

**Prompt:**
> Write Python code to encrypt sensitive data at rest. The ciphertext must be tamper-evident, and the encryption key must not be hardcoded.

**Elite Implementation:**

```python
"""
Authenticated encryption with AES-256-GCM.
Principles: Boneh (AEAD is the minimum viable primitive — confidentiality
            without integrity is not secure); Green (never roll your own
            crypto; nonce reuse is catastrophic); Kerckhoffs (algorithm is
            public, key is secret); Schneier (key management is the hard part).
"""
import os
import base64
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# ── Key management ─────────────────────────────────────────────────────────
# Principle: Never embed secrets — key material comes from environment or KMS.
# In production, use AWS KMS / GCP KMS / HashiCorp Vault envelope encryption.
# Here we demonstrate direct key usage from environment.

def _load_key() -> bytes:
    """
    Load a 32-byte (256-bit) AES key from the environment.
    The value must be base64-encoded in the environment variable.
    """
    raw = os.environ.get("ENCRYPTION_KEY_B64")
    if not raw:
        raise RuntimeError(
            "ENCRYPTION_KEY_B64 not set. "
            "Generate with: python -c \"import os,base64; "
            "print(base64.b64encode(os.urandom(32)).decode())\""
        )
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise ValueError(f"Key must be 256 bits (32 bytes), got {len(key)}")
    return key


# ── Context-specific subkey derivation (optional but recommended) ──────────
def _derive_subkey(master_key: bytes, context: bytes) -> bytes:
    """
    Derive a purpose-specific subkey via HKDF-SHA256.
    Principle: Separation of privilege / key isolation — using the same key
    for multiple purposes creates cross-context attack vectors.
    """
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,         # HKDF extracts from master; salt adds entropy if available
        info=context,      # domain-separates keys: b"email-encrypt" vs b"db-encrypt"
    ).derive(master_key)


# ── Wire format: nonce (12 bytes) ‖ ciphertext+tag ─────────────────────────
# The 16-byte GCM authentication tag is appended by the library to ciphertext.
# We prepend the nonce so the decryptor always has it.

def encrypt(plaintext: bytes, *, context: bytes = b"default") -> bytes:
    """
    Encrypt plaintext with AES-256-GCM.
    Returns:  nonce (12 bytes) || ciphertext || auth_tag (16 bytes)

    Principle: Every call generates a fresh nonce from CSPRNG.
    Matt Green's rule: "NEVER REUSE A NONCE with a key" — GCM nonce reuse
    leaks the key stream and allows forging of any ciphertext.
    """
    master_key = _load_key()
    subkey = _derive_subkey(master_key, context)

    # Principle: CSPRNG for nonce — never counter, never timestamp, never zero
    nonce = os.urandom(12)   # 96-bit nonce, NIST-recommended for GCM

    aesgcm = AESGCM(subkey)

    # encrypt() returns ciphertext || 16-byte tag (tag is appended automatically)
    ciphertext_with_tag = aesgcm.encrypt(
        nonce,
        plaintext,
        None,   # no additional authenticated data here; pass context bytes if needed
    )

    # Wire: nonce (12) || ciphertext+tag (variable)
    return nonce + ciphertext_with_tag


def decrypt(token: bytes, *, context: bytes = b"default") -> bytes:
    """
    Decrypt and authenticate.
    Raises cryptography.exceptions.InvalidTag if tampered.
    Principle: Fail closed — tampered ciphertext raises, never returns garbage.
    """
    if len(token) < 12 + 16:   # nonce + minimum 1-byte plaintext + 16-byte tag
        raise ValueError("Token too short to be valid ciphertext")

    nonce = token[:12]
    ciphertext_with_tag = token[12:]

    master_key = _load_key()
    subkey = _derive_subkey(master_key, context)
    aesgcm = AESGCM(subkey)

    # Principle: Fail closed — AESGCM.decrypt() raises InvalidTag if the
    # ciphertext or nonce was modified; we let that exception propagate.
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


# ── Usage ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    secret = b"SSN: 123-45-6789"
    token = encrypt(secret, context=b"pii-field")
    recovered = decrypt(token, context=b"pii-field")
    assert recovered == secret

# ── NEVER DO THIS ──────────────────────────────────────────────────────────
#
# BAD: AES-CBC without MAC → malleable, no integrity
#   from Crypto.Cipher import AES
#   cipher = AES.new(key, AES.MODE_CBC, iv)
#   ct = cipher.encrypt(pad(data, AES.block_size))
#
# BAD: hardcoded key
#   KEY = b"mysecretkey12345"
#
# BAD: reused nonce
#   FIXED_NONCE = b"\x00" * 12
#   ct = aesgcm.encrypt(FIXED_NONCE, data, None)
#
# BAD: home-grown XOR cipher
#   ciphertext = bytes(a ^ b for a, b in zip(data, key_repeated))
```

---

### Gold Example 3 — Secure Session Management & CSRF Defense

**Prompt:**
> Implement secure login and logout for a Flask web application with proper session handling, CSRF protection, and secure cookie settings.

**Elite Implementation:**

```python
"""
Secure session management for Flask.
Principles: Saltzer-Schroeder (fail-safe defaults, complete mediation,
            psychological acceptability); OWASP A07 (authentication failures);
            Schneier (security is a process — sessions must be invalidated
            server-side); Bellovin (protocol design is where auth breaks).
"""
import os
import secrets
import time
from functools import wraps
from flask import Flask, request, session, redirect, url_for, abort, g
import redis  # server-side session store

app = Flask(__name__)

# Principle: Never embed secrets
app.secret_key = os.environ["FLASK_SECRET_KEY"]   # 32+ random bytes, base64

# Secure cookie configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,     # No JS access — mitigates XSS theft
    SESSION_COOKIE_SECURE=True,       # HTTPS only — no cleartext transmission
    SESSION_COOKIE_SAMESITE="Strict", # CSRF mitigation at cookie layer
    SESSION_COOKIE_NAME="__Host-sid", # __Host- prefix enforces Secure + no Domain
    PERMANENT_SESSION_LIFETIME=1800,  # 30-minute idle timeout
)

# Server-side session store (principle: complete mediation — revocation is instant)
_redis = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
_SESSION_TTL = 1800          # seconds
_CSRF_TOKEN_BYTES = 32


# ── CSRF token helpers ─────────────────────────────────────────────────────

def _generate_csrf_token() -> str:
    """
    Principle: CSPRNG for security tokens.
    secrets.token_hex uses os.urandom — cryptographically random.
    Never use random.token_hex or uuid4 for CSRF tokens.
    """
    return secrets.token_hex(_CSRF_TOKEN_BYTES)


def _validate_csrf(form_token: str, session_token: str) -> bool:
    """
    Principle: Timing-safe comparison.
    hmac.compare_digest prevents timing oracle that reveals partial match.
    Python's == on strings short-circuits — leaks length information.
    """
    import hmac as _hmac
    if not form_token or not session_token:
        return False
    return _hmac.compare_digest(form_token, session_token)


# ── Server-side session store ──────────────────────────────────────────────

def _create_server_session(user_id: int, role: str) -> str:
    """
    Store session data server-side; only the opaque token goes to client.
    Principle: Economy of mechanism — cookie holds only a random handle,
    not the authoritative data (prevents client-side tampering).
    """
    sid = secrets.token_hex(32)       # 256-bit opaque session identifier
    csrf_token = _generate_csrf_token()
    _redis.setex(
        f"session:{sid}",
        _SESSION_TTL,
        f"{user_id}:{role}:{csrf_token}:{int(time.time())}",
    )
    return sid, csrf_token


def _get_server_session(sid: str) -> dict | None:
    """
    Retrieve and validate a server-side session.
    Principle: Complete mediation — every request checks server-side store.
    """
    if not sid or len(sid) != 64:    # 32-byte hex = 64 chars
        return None
    raw = _redis.get(f"session:{sid}")
    if not raw:
        return None
    parts = raw.split(":")
    if len(parts) != 4:
        return None
    user_id, role, csrf_token, created_at = parts
    return {
        "user_id": int(user_id),
        "role": role,
        "csrf_token": csrf_token,
        "created_at": int(created_at),
    }


def _destroy_server_session(sid: str) -> None:
    """
    Principle: Complete mediation — logout must invalidate server-side.
    Deleting only the cookie still leaves the session valid if sniffed.
    """
    _redis.delete(f"session:{sid}")


# ── Authentication decorator ───────────────────────────────────────────────

def login_required(f):
    """
    Principle: Fail-safe defaults — missing or invalid session → 401.
    Complete mediation — checks server-side store, not just cookie presence.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        sid = request.cookies.get("__Host-sid")
        sess = _get_server_session(sid) if sid else None
        if not sess:
            return redirect(url_for("login"))
        g.session = sess   # attach to request context, not global state
        return f(*args, **kwargs)
    return decorated


def csrf_protect(f):
    """
    Principle: Separation of privilege — state-changing requests require
    both a valid session AND a valid CSRF token. Absence of either = deny.
    Synchroniser token pattern (OWASP recommended).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sid = request.cookies.get("__Host-sid")
            sess = _get_server_session(sid) if sid else None
            form_token = request.form.get("csrf_token") or request.headers.get(
                "X-CSRF-Token"
            )
            if not sess or not _validate_csrf(form_token, sess["csrf_token"]):
                abort(403)   # Fail closed
        return f(*args, **kwargs)
    return decorated


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Principle: Input validation before any auth logic
        if not (1 <= len(username) <= 64) or not (8 <= len(password) <= 1024):
            return "Invalid input", 400

        # lookup_user() from Gold Example 1 — parameterised, timing-safe
        from auth import lookup_user
        user = lookup_user(username, password)

        if user is None:
            # Principle: Fail closed — uniform error, no oracle
            # Uniform delay prevents timing enumeration (or use Argon2 dummy)
            return "Invalid credentials", 401

        sid, csrf_token = _create_server_session(user["id"], user["role"])

        response = redirect(url_for("dashboard"))
        response.set_cookie(
            "__Host-sid",
            sid,
            max_age=_SESSION_TTL,
            secure=True,
            httponly=True,
            samesite="Strict",
        )
        return response

    return """
    <form method="post">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input name="username"> <input name="password" type="password">
        <button>Login</button>
    </form>
    """


@app.route("/logout", methods=["POST"])
@login_required
@csrf_protect
def logout():
    sid = request.cookies.get("__Host-sid")
    # Principle: Complete mediation — destroy server-side, don't just clear cookie
    _destroy_server_session(sid)
    response = redirect(url_for("login"))
    response.delete_cookie("__Host-sid")
    return response


@app.route("/dashboard")
@login_required
def dashboard():
    return f"Hello, user {g.session['user_id']}"


# ── NEVER DO THIS ──────────────────────────────────────────────────────────
#
# BAD: session data in signed cookie only (client can't tamper, but can replay)
#   session["user_id"] = user_id    # if Flask session only, no server revocation
#
# BAD: no HttpOnly / Secure flags
#   response.set_cookie("sid", value)
#
# BAD: CSRF token with random.random()
#   csrf = str(random.random())
#
# BAD: == to compare CSRF tokens
#   if request.form["csrf_token"] == session["csrf_token"]:  # timing oracle
```

---

### Gold Example 4 — Input Validation with Defense in Depth

**Prompt:**
> Write a Python function that accepts a user-submitted filename and returns the file contents from a predefined upload directory. Make it secure.

**Elite Implementation:**

```python
"""
Safe file access with path traversal and allowlist defense.
Principles: Saltzer-Schroeder (complete mediation, fail-safe defaults,
            least privilege); OWASP A01 (broken access control);
            Thompson (never trust the path — compiler lesson generalised);
            Aleph One (understanding attacker goal = bypass the check).
"""
import os
import re
import pathlib
from typing import Optional

# Principle: Least Privilege — the server process only has read access
# to this single directory; it cannot access /etc, /home, or parent dirs.
_UPLOAD_DIR = pathlib.Path(os.environ.get("UPLOAD_DIR", "/var/uploads")).resolve()

# Allowlist of permitted extensions (principle: allowlist > denylist)
_ALLOWED_EXTENSIONS = frozenset({".txt", ".csv", ".json", ".pdf"})

# Max filename length (principle: validate all dimensions)
_MAX_FILENAME_LEN = 128


def read_upload(raw_filename: str) -> bytes:
    """
    Securely read a file from the upload directory.
    Raises ValueError for any invalid/unsafe input.
    Raises FileNotFoundError if file does not exist.
    Never traverses outside _UPLOAD_DIR.

    Defense in depth:
      Layer 1 — Type and length check (fast reject)
      Layer 2 — Allowlist regex on filename characters
      Layer 3 — Extension allowlist
      Layer 4 — Path resolution + prefix assertion (canonical path jail)
    """

    # Layer 1: Type and length
    if not isinstance(raw_filename, str):
        raise ValueError("Filename must be a string")
    if not (1 <= len(raw_filename) <= _MAX_FILENAME_LEN):
        raise ValueError(f"Filename length must be 1–{_MAX_FILENAME_LEN} chars")

    # Layer 2: Allowlist regex — only safe characters
    # Rejects: ..  /  \  NUL  %  :  null bytes, Unicode tricks
    # Principle: Allowlist known-good; reject everything else
    if not re.fullmatch(r"[A-Za-z0-9_\-][A-Za-z0-9_\-\.]{0,126}", raw_filename):
        raise ValueError("Filename contains disallowed characters")

    # Layer 3: Extension must be in allowed set
    suffix = pathlib.PurePosixPath(raw_filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension '{suffix}' not permitted")

    # Layer 4: Path jail — resolve to absolute, assert it stays under UPLOAD_DIR
    # This defeats: "../../../etc/passwd", symlink attacks, encoded slashes
    # pathlib.resolve() follows symlinks and returns the real canonical path
    candidate = (_UPLOAD_DIR / raw_filename).resolve()

    # Principle: Complete mediation — check AFTER resolution, not before
    # Checking the raw string before resolution would allow symlink bypass
    if not str(candidate).startswith(str(_UPLOAD_DIR) + os.sep):
        raise ValueError("Path traversal detected")

    # Principle: Fail closed — if resolve() somehow yields a non-file, raise
    if not candidate.is_file():
        raise FileNotFoundError(f"No such file: {raw_filename!r}")

    # Principle: Least common mechanism — open with restricted mode
    # No execute, no write; read-only, binary mode
    with candidate.open("rb") as fh:
        return fh.read()


# ── NEVER DO THIS ──────────────────────────────────────────────────────────
#
# BAD: path join without resolution check
#   path = os.path.join(UPLOAD_DIR, filename)
#   # filename = "../../etc/passwd" → /var/uploads/../../etc/passwd → /etc/passwd
#   with open(path) as f: return f.read()
#
# BAD: denylist instead of allowlist
#   if ".." in filename:   # attacker uses URL-encoding: %2e%2e or unicode %c0%ae
#       raise ValueError("bad path")
#
# BAD: no extension check
#   path = UPLOAD_DIR / filename  # allows .py, .sh, .so upload
#
# BAD: check before resolve (TOCTTOU race)
#   if filename.startswith("/"):
#       raise ValueError()
#   path = resolve(UPLOAD_DIR / filename)  # race: symlink injected between check+open
```

---

### Gold Example 5 — Cryptographically Secure Token Generation & Secrets Hygiene

**Prompt:**
> Write a Python function to generate a password-reset token, store it, and validate it when the user submits it — with appropriate expiry and security.

**Elite Implementation:**

```python
"""
Password-reset token lifecycle.
Principles: Schneier (security as process — tokens must expire and be
            one-time use); Kocher (timing-safe comparison); Boneh (HMAC
            for server-side integrity, not encrypting random tokens);
            OWASP A07 (authentication failures); Green (CSPRNG always).
"""
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional
import redis  # ephemeral, server-authoritative store

_redis = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

# Principle: Never embed secrets
_HMAC_KEY = os.environ["TOKEN_HMAC_KEY"].encode()   # 32+ random bytes

_TOKEN_BYTES = 32        # 256 bits of entropy
_TOKEN_TTL = 900         # 15 minutes
_MAX_ATTEMPTS = 3        # Principle: Fail closed after brute-force attempts


@dataclass
class TokenIssueResult:
    """Return type — never return raw token embedded in a URL in logs."""
    token: str           # send to user via email, never log this
    user_id: int


def issue_reset_token(user_id: int) -> TokenIssueResult:
    """
    Generate and store a one-time password-reset token.

    Design:
    - Token has 256 bits of CSPRNG entropy (not guessable).
    - HMAC binds token to user_id (prevents token-swapping across accounts).
    - Only HMAC digest is stored (server never stores raw token — breach of
      Redis does not yield usable tokens without _HMAC_KEY).
    - TTL enforced at storage layer (Redis SETEX).
    - Principle: Invalidate any existing token for user (one token active at once).
    """

    # Principle: CSPRNG — secrets module uses os.urandom internally
    raw_token = secrets.token_urlsafe(_TOKEN_BYTES)   # 256-bit, URL-safe base64

    # Bind token to user_id via HMAC to prevent cross-account swap
    digest = hmac.new(
        _HMAC_KEY,
        f"{user_id}:{raw_token}".encode(),
        hashlib.sha256,
    ).hexdigest()

    # Principle: Least common mechanism — store digest, not raw token
    # A Redis breach leaks digests; without _HMAC_KEY they are unusable
    key = f"pwr:{user_id}"
    pipe = _redis.pipeline()
    pipe.setex(key, _TOKEN_TTL, f"{digest}:0")   # value = digest:attempt_count
    pipe.execute()

    return TokenIssueResult(token=raw_token, user_id=user_id)


def validate_reset_token(user_id: int, submitted_token: str) -> bool:
    """
    Validate a reset token.
    Returns True iff: token exists, not expired, attempt count < limit,
    and HMAC matches.
    Side effects: increments attempt counter; deletes token on success.

    Principles:
    - Timing-safe comparison (hmac.compare_digest) throughout.
    - Fail closed: any error → False (never open).
    - Brute-force limit: max 3 attempts before token is invalidated.
    - One-time use: successful validation deletes the token.
    """

    # Input validation (principle: fail fast on garbage input)
    if not isinstance(submitted_token, str) or not (40 <= len(submitted_token) <= 100):
        return False
    if not isinstance(user_id, int) or user_id < 1:
        return False

    key = f"pwr:{user_id}"
    raw = _redis.get(key)

    if not raw:
        # Principle: Normalise timing — perform dummy HMAC to avoid oracle
        hmac.new(_HMAC_KEY, b"dummy:dummy", hashlib.sha256).hexdigest()
        return False

    parts = raw.split(":")
    if len(parts) != 2:
        return False

    stored_digest, attempt_str = parts
    try:
        attempts = int(attempt_str)
    except ValueError:
        return False

    # Principle: Fail closed after brute-force threshold
    if attempts >= _MAX_ATTEMPTS:
        _redis.delete(key)    # invalidate exhausted token
        return False

    # Recompute HMAC of submitted token to compare
    candidate_digest = hmac.new(
        _HMAC_KEY,
        f"{user_id}:{submitted_token}".encode(),
        hashlib.sha256,
    ).hexdigest()

    # Principle: Timing-safe comparison — compare_digest is constant time
    # regardless of where the strings first differ
    if hmac.compare_digest(stored_digest, candidate_digest):
        # One-time use: delete immediately on success
        _redis.delete(key)
        return True
    else:
        # Increment attempt counter (brute-force mitigation)
        _redis.setex(
            key,
            int(_redis.ttl(key)) or _TOKEN_TTL,   # preserve remaining TTL
            f"{stored_digest}:{attempts + 1}",
        )
        return False


# ── NEVER DO THIS ──────────────────────────────────────────────────────────
#
# BAD: uuid4 token (not CSPRNG-backed in all implementations, too short)
#   import uuid; token = str(uuid.uuid4())
#
# BAD: store raw token in DB → breach yields usable tokens
#   db.execute("INSERT INTO tokens (user_id, token) VALUES (?, ?)", (uid, raw))
#
# BAD: == comparison → timing oracle reveals partial match
#   if stored_token == submitted_token:
#
# BAD: no expiry → tokens valid forever
#   db.execute("SELECT * FROM tokens WHERE token = ?", (submitted,))
#
# BAD: no one-time use → token reusable after first legitimate reset
```

---

## 4. ELITE AUDIT FUNCTION

The following Python pseudocode gates eliteness. Apply it to any candidate security answer
before accepting it as gold. A single FAIL is disqualifying unless the principle genuinely
does not apply (e.g., a read-only query cannot embed secrets in its output).

```python
"""
Elite Security Audit — Python pseudocode.
Returns list of violations. Empty list = candidate passes.
Principles: systematises the criteria from Section 2.
"""
import ast
import re
import hashlib

# ── Hardcoded-secret patterns ──────────────────────────────────────────────
_SECRET_PATTERNS = [
    # API keys, tokens, passwords, private keys hardcoded as literals
    re.compile(r'(?i)(password|passwd|secret|api_key|apikey|token|private_key'
               r'|aws_secret|auth_token)\s*=\s*["\'][^${\s]{6,}["\']'),
    # Hardcoded connection strings
    re.compile(r'(?i)(postgresql|mysql|mongodb|redis)://[^{][^@]+@'),
    # BEGIN RSA/EC PRIVATE KEY in string
    re.compile(r'-----BEGIN\s+(?:RSA|EC|OPENSSH|DSA)\s+PRIVATE KEY-----'),
    # AWS-style secrets
    re.compile(r'(?i)AKIA[0-9A-Z]{16}'),
]

# ── Weak / forbidden crypto identifiers ───────────────────────────────────
_WEAK_CRYPTO = {
    "md5", "sha1", "des", "rc4", "ecb", "rot13",
    "base64",       # base64 is encoding, not encryption — flag if used as "encryption"
    "random",       # built-in random module is not CSPRNG
}

# ── Injection-risk patterns ────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    # SQL: f-string or % with variable in a query-looking context
    re.compile(r'(?i)(execute|query|cursor\.execute)\s*\(\s*f["\']'),
    re.compile(r'(?i)(execute|query)\s*\(\s*"[^"]*%s[^"]*"\s*%\s*(?![\(])'),
    # Shell injection: os.system or subprocess.call with string concat
    re.compile(r'os\.system\s*\(\s*f["\']'),
    re.compile(r'subprocess\.(call|run|Popen)\s*\([^,]*\+'),
]

# ── Non-constant-time comparison ───────────────────────────────────────────
_TIMING_RISK = re.compile(
    r'==\s*["\']|["\'][^"\']*["\'\s]==|digest\s*==|hash\s*==|token\s*=='
)

# ── Missing AEAD / bare encryption ────────────────────────────────────────
_BARE_ENCRYPTION = re.compile(
    r'(?i)AES\.(MODE_CBC|MODE_CTR|MODE_ECB|MODE_CFB)(?!\s*with\s*HMAC)'
)

# ── Repetition / degeneration guard ───────────────────────────────────────
def _degeneration_check(code: str) -> list[str]:
    """
    Detect degeneration (repetition, stubbing, placeholder, truncation).
    An elite answer is complete and non-repetitive.
    """
    violations = []
    lines = code.strip().splitlines()

    # Truncation: suspiciously short for a "complete" implementation
    if len(lines) < 10:
        violations.append("DEGENERATE: Answer is shorter than 10 lines — likely truncated or stubbed")

    # Placeholder comments masquerading as implementation
    placeholder_patterns = [
        re.compile(r'(?i)(TODO|FIXME|pass\s*#\s*implement|raise\s+NotImplementedError)'),
        re.compile(r'(?i)#\s*(your code here|add implementation|fill in|stub)'),
    ]
    for pat in placeholder_patterns:
        if any(pat.search(line) for line in lines):
            violations.append("DEGENERATE: Placeholder or stub detected — not a complete implementation")

    # Repetition: same substantive line appearing 3+ times
    from collections import Counter
    stripped = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    counts = Counter(stripped)
    repeated = [line for line, cnt in counts.items() if cnt >= 3 and len(line) > 20]
    if repeated:
        violations.append(f"DEGENERATE: Repeated lines detected: {repeated[:2]}")

    return violations


def audit_security_answer(code: str, context: str = "") -> list[str]:
    """
    Audit a candidate security implementation.

    Args:
        code:    the candidate's Python source code as a string
        context: brief description of what the code claims to do

    Returns:
        List of violation strings. Empty list = passes all checks.
    """
    violations = []

    # 1. Hardcoded secrets
    for pat in _SECRET_PATTERNS:
        matches = pat.findall(code)
        if matches:
            violations.append(
                f"FAIL[hardcoded-secret]: Pattern matched: {matches[0]!r} — "
                "secrets must come from environment or secrets manager, never source"
            )

    # 2. Injection risk
    for pat in _INJECTION_PATTERNS:
        if pat.search(code):
            violations.append(
                "FAIL[injection]: String-concatenated query detected. "
                "Use parameterised queries / placeholders only."
            )

    # 3. Weak crypto
    code_lower = code.lower()
    for weak in _WEAK_CRYPTO:
        # Detect import or use, but allow "hmac" (which contains 'md5' as part of algo name)
        if re.search(rf'\b{weak}\b', code_lower):
            # Allow md5/sha1 when used for non-security checksums (file dedupe, ETag)
            # but flag them in authentication/encryption/password contexts
            if any(kw in context.lower() for kw in ("auth", "password", "encrypt", "token", "sign")):
                violations.append(
                    f"FAIL[weak-crypto]: '{weak}' used in security-sensitive context. "
                    "Use Argon2id for passwords; AES-256-GCM or ChaCha20-Poly1305 for encryption; "
                    "SHA-256+ for HMAC."
                )

    # 4. Timing-unsafe comparison
    if _TIMING_RISK.search(code) and "hmac.compare_digest" not in code:
        violations.append(
            "FAIL[timing-oracle]: Direct == comparison of secrets or hashes detected. "
            "Use hmac.compare_digest() for constant-time comparison."
        )

    # 5. Bare encryption (no integrity)
    if _BARE_ENCRYPTION.search(code):
        violations.append(
            "FAIL[no-integrity]: Bare symmetric encryption without authentication "
            "(AES-CBC/CTR/ECB without MAC). Use AES-GCM or ChaCha20-Poly1305 (AEAD)."
        )

    # 6. Non-CSPRNG for secrets
    if re.search(r'\brandom\.(random|randint|choice|uniform|randrange)\b', code):
        if any(kw in context.lower() for kw in ("token", "secret", "nonce", "key", "session", "csrf")):
            violations.append(
                "FAIL[weak-rng]: random module (non-CSPRNG) used for security-sensitive value. "
                "Use secrets module or os.urandom()."
            )

    # 7. Missing fail-closed pattern
    # Heuristic: if the code handles auth/session but has no explicit deny-by-default
    if any(kw in context.lower() for kw in ("auth", "login", "session", "access")):
        if "return False" not in code and "return None" not in code and "abort(" not in code:
            violations.append(
                "WARN[fail-open]: No explicit fail-closed return detected in auth context. "
                "Ensure every error/ambiguity path denies access explicitly."
            )

    # 8. Open design / Kerckhoffs violation (security by obscurity)
    if re.search(r'(?i)(obfuscat|obscur|secret.?algorithm|custom.?cipher|proprietary.?crypto)', code):
        violations.append(
            "FAIL[obscurity]: Code appears to rely on algorithm secrecy. "
            "Per Kerckhoffs: security must reside in the key, never the algorithm."
        )

    # 9. Degeneration / repetition guard
    violations.extend(_degeneration_check(code))

    return violations


# ── Example usage ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test: a clearly bad candidate
    bad_code = """
import hashlib

PASSWORD_DB_SECRET = "hunter2secret"
conn_string = "postgresql://admin:password123@localhost/app"

def check_login(username, password):
    import sqlite3
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE username = '{username}'")
    row = cur.fetchone()
    stored_hash = hashlib.md5(password.encode()).hexdigest()
    return row and stored_hash == row["password_hash"]
"""
    results = audit_security_answer(bad_code, context="authentication login")
    print("Violations found:")
    for v in results:
        print(" •", v)
    # Expected: hardcoded-secret (×2), injection, weak-crypto (md5), timing-oracle

    # Test: a clean candidate (simplified)
    good_code = """
import os
import hmac
from argon2 import PasswordHasher
import psycopg2

_PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_DSN = os.environ["DATABASE_URL"]

def check_login(username, password):
    conn = psycopg2.connect(_DSN)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    if not row:
        return None
    try:
        _PH.verify(row[0], password)
        return True
    except Exception:
        return None
"""
    results = audit_security_answer(good_code, context="authentication login")
    if not results:
        print("\nClean candidate: PASSES audit")
    else:
        print("\nClean candidate violations:", results)
```

---

## References & Grounding

Sources that ground this document in named elites:

- Saltzer & Schroeder (1975), *The Protection of Information in Computer Systems*, Proc. IEEE
- Kerckhoffs (1883), *La Cryptographie Militaire*, Journal des Sciences Militaires
- Shannon (1949), *Communication Theory of Secrecy Systems*, Bell System Technical Journal
- Diffie & Hellman (1976), *New Directions in Cryptography*, IEEE Transactions on Information Theory
- Rivest, Shamir, Adleman (1977), MIT Lab for Computer Science, Technical Memo 82
- Clifford Cocks, GCHQ (1973, declassified 1997) — public-key encryption three years before RSA
- Dorothy Denning (1976), *A Lattice Model of Secure Information Flow*, Comm. ACM
- Ken Thompson (1984), *Reflections on Trusting Trust*, Turing Award Lecture, Comm. ACM
- Aleph One (1996), *Smashing the Stack for Fun and Profit*, Phrack Magazine #49
- Bruce Schneier (2000), *Secrets and Lies: Digital Security in a Networked World*; schneier.com — Schneier's Law
- Ross Anderson (2020), *Security Engineering* 3rd ed., Wiley
- Bellovin & Cheswick (1994), *Firewalls and Internet Security: Repelling the Wily Hacker*
- Paul Kocher (1996), *Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS...*, CRYPTO; Kocher, Jaffe, Jun (1998), *Introduction to DPA*
- Dan Boneh & Victor Shoup, *A Graduate Course in Applied Cryptography*, Stanford (crypto.stanford.edu/~dabo)
- Matt Green, *A Few Thoughts on Cryptographic Engineering*, blog.cryptographyengineering.com
- Halvar Flake (Thomas Dullien), Black Hat Briefings 2008–2017; HITB 2018 — binary analysis & vulnerability research
- OWASP Foundation, *Top 10:2021* (owasp.org); *Input Validation Cheat Sheet*; *CSRF Prevention Cheat Sheet*
- Python `cryptography` library docs — `cryptography.io/en/latest/hazmat/primitives/aead/`
- Python `secrets` module — `docs.python.org/3/library/secrets.html`
- NIST SP 800-38D (GCM mode, nonce guidance)
- RFC 9106 (Argon2, 2021)
