"""Symmetric encryption for sensitive data at rest.

Uses Fernet symmetric encryption with a key derived from the application's
SECRET_KEY. This protects webhook secrets and other sensitive values stored
in the database.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from dataseal.config import settings

_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    """Get or create a Fernet instance using a key derived from SECRET_KEY."""
    global _fernet_instance
    if _fernet_instance is None:
        # Derive a 32-byte key from SECRET_KEY using SHA-256, then base64 encode
        # for Fernet (which requires a 32-byte URL-safe base64-encoded key)
        derived = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(derived)
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value and return the ciphertext as a base64 string.

    Args:
        plaintext: The value to encrypt.

    Returns:
        The encrypted value as a URL-safe base64 string.
    """
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a previously encrypted value.

    Args:
        ciphertext: The encrypted value as returned by encrypt_value().

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If the ciphertext is invalid or tampered with.
    """
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Cannot decrypt value: invalid token or wrong key")
