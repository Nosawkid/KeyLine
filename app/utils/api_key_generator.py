import secrets


def generate_api_key() -> tuple[str, str]:
    """Return a key and a non-secret lookup prefix shared by key and database row."""
    random_value = secrets.token_urlsafe(32)
    key = f"sk_live_{random_value}"
    return key, key[:16]
