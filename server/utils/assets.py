import base64
import hashlib


def hash_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode("utf-8")
