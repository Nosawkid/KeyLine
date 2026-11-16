from datetime import UTC, datetime, timedelta
import hashlib
import hmac
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> UUID:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return UUID(payload["sub"])


def hash_api_key(api_key: str) -> str:
    secret = get_settings().api_key_hmac_secret.encode()
    return hmac.new(secret, api_key.encode(), hashlib.sha256).hexdigest()


def api_key_matches(api_key: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), expected_hash)
