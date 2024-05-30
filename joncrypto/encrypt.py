import json
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import padding

class enc:
    def __init__(self, key):
        self.key = key
        self.fernet = Fernet(key)

    def encrypt_json(self, json_data):
        # Layer 1: JSON to bytes
        json_bytes = json.dumps(json_data).encode("utf-8")

        # Layer 2: Base64 encoding
        base64_bytes = base64.b64encode(json_bytes)

        # Layer 3: SHA-256 hashing
        sha256_hash = hashlib.sha256(base64_bytes).digest()

        # Layer 4: Fernet encryption
        encrypted_bytes = self.fernet.encrypt(sha256_hash)

        # Add padding to ensure the encrypted data is a multiple of 16 bytes
        padder = padding.PKCS7(128).padder()
        padded_bytes = padder.update(encrypted_bytes) + padder.finalize()

        return padded_bytes

    def export_to_ndb(self, encrypted_bytes, filename):
        with open(filename, "wb") as f:
            f.write(encrypted_bytes)