import json
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import padding

class encrypt:
    def encrypt_json(self, json_data, key):
        # Pad the key to be URL-safe
        key = base64.urlsafe_b64encode(key.encode()).decode()

        # Layer 1: JSON to bytes
        json_bytes = json.dumps(json_data).encode("utf-8")

        # Layer 2: Base64 encoding
        base64_bytes = base64.b64encode(json_bytes)

        # Layer 3: SHA-256 hashing
        sha256_hash = hashlib.sha256(base64_bytes).digest()

        # Layer 4: Fernet encryption
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(sha256_hash)

        # Add padding to ensure the encrypted data is a multiple of 16 bytes
        padder = padding.PKCS7(128).padder()
        padded_bytes = padder.update(encrypted_bytes) + padder.finalize()

        return padded_bytes
    def export_to_ndb(self, encrypted_bytes, filename):
        with open(filename, "wb") as f:
            f.write(encrypted_bytes)

class decrypt:
    def import_from_ndb(self, filename):
        with open(filename, "rb") as f:
            encrypted_bytes = f.read()
        return encrypted_bytes

    def decrypt_json(self, encrypted_bytes, key):
        # Remove padding
        try:
            unpadder = padding.PKCS7(128).unpadder()
            unpadded_bytes = unpadder.update(encrypted_bytes) + unpadder.finalize()
        except ValueError:
            # Invalid padding bytes
            return None

        # Layer 4: Fernet decryption
        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(unpadded_bytes)
        # Layer 3: SHA-256 hash verification
        sha256_hash = decrypted_bytes

        # Layer 2: Base64 decoding
        base64_bytes = sha256_hash
        json_bytes = base64.b64decode(base64_bytes)

        # Layer 1: JSON to object
        try:
            json_data = json.loads(json_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            # Corrupted JSON data
            return None

        return json_data
class data:
    def __init__(self, database_name, key):
        self.database_name = database_name
        self.database_path = f"./databases/{database_name}"
        if not os.path.exists(self.database_path):
            os.makedirs(self.database_path)

        self.key_base64 = self._generate_key_base64(key)
        self.fernet = Fernet(self.key_base64)

    def _generate_key_base64(self, key):
        # Pad the key to be URL-safe
        key = base64.urlsafe_b64encode(key.encode()).decode()
        return key
    

    def create_collection(self, collection_name):
        collection_path = f"{self.database_path}/{collection_name}.json"
        if not os.path.exists(collection_path):
            with open(collection_path, "w") as collection_file:
                collection_file.write("[]")

    def read_collection(self, collection_name):
        global key
        collection_path = f"{self.database_path}/{collection_name}.json"
        with open(collection_path, "rb") as collection_file:  # Open the file in binary mode
            encrypted_data = collection_file.read()
            decrypted_data = decrypt().decrypt_json(encrypted_data, key)
            if decrypted_data is None:
                return []  # or raise an exception, depending on your requirements
            return json.loads(decrypted_data)

    def write_collection(self, collection_name, data):
        global key
        collection_path = f"{self.database_path}/{collection_name}.json"
        with open(collection_path, "w") as collection_file:
            encrypted_data = encrypt().encrypt_json(data, key)
            encrypt().export_to_ndb(encrypted_data, collection_path)

    def add_document(self, collection_name, document):
        collection = self.read_collection(collection_name)
        document["id"] = len(collection)
        collection.append(document)
        self.write_collection(collection_name, collection)

    def find_document(self, collection_name, query):
        collection = self.read_collection(collection_name)
        return [document for document in collection if document.get(query["field"]) == query["value"]]

    def update_document(self, collection_name, query, new_data):
        collection = self.read_collection(collection_name)
        for index, document in enumerate(collection):
            if document.get(query["field"]) == query["value"]:
                collection[index].update(new_data)
                break
        self.write_collection(collection_name, collection)

    def delete_document(self, collection_name, query):
        collection = self.read_collection(collection_name)
        collection = [document for document in collection if document.get(query["field"]) != query["value"]]
        self.write_collection(collection_name, collection)

    def link_collections(self, collection1_name, collection2_name, field1, field2):
        collection1 = self.read_collection(collection1_name)
        collection2 = self.read_collection(collection2_name)
        for document1 in collection1:
            if field1 in document1:
                document1[field2] = [document2 for document2 in collection2 if document2[field2] == document1[field1]]
        self.write_collection(collection1_name, collection1)