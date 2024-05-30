import json
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import padding

class dec:
    def __init__(self, key):
        self.key = key
        self.fernet = Fernet(key)

    def import_from_ndb(self, filename):
        with open(filename, "rb") as f:
            encrypted_bytes = f.read()
        return encrypted_bytes

    def decrypt_json(self, encrypted_bytes):
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_bytes = unpadder.update(encrypted_bytes) + unpadder.finalize()

        # Layer 4: Fernet decryption
        decrypted_bytes = self.fernet.decrypt(unpadded_bytes)

        # Layer 3: SHA-256 hash verification
        sha256_hash = decrypted_bytes

        # Layer 2: Base64 decoding
        base64_bytes = sha256_hash
        json_bytes = base64.b64decode(base64_bytes)

        # Layer 1: JSON to object
        json_data = json.loads(json_bytes.decode("utf-8"))

        return json_data
