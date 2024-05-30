import json
import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken

# logging.basicConfig(level=logging.DEBUG)

class Encrypt:
    @staticmethod
    def generate_fernet_key(key):
        # Generate Fernet key from the provided key
        return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())

    def encrypt_json(self, json_data, key):
        fernet_key = self.generate_fernet_key(key)
        fernet = Fernet(fernet_key)

        # JSON to bytes
        json_bytes = json.dumps(json_data).encode("utf-8")

        # Fernet encryption
        encrypted_bytes = fernet.encrypt(json_bytes)
        logging.debug(f"Encrypted bytes: {encrypted_bytes}")

        # Second layer of encryption
        second_layer_encrypted_bytes = fernet.encrypt(encrypted_bytes)
        logging.debug(f"Second layer encrypted bytes: {second_layer_encrypted_bytes}")

        # Convert to binary string
        binary_string = ''.join(format(byte, '08b') for byte in second_layer_encrypted_bytes)
        logging.debug(f"Binary string: {binary_string}")

        return binary_string.encode('utf-8')

    def export_to_ndb(self, binary_string, filename):
        with open(filename, "wb") as f:
            f.write(binary_string)

class Decrypt:
    @staticmethod
    def generate_fernet_key(key):
        # Generate Fernet key from the provided key
        return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())

    def import_from_ndb(self, filename):
        with open(filename, "rb") as f:
            binary_string = f.read()
        return binary_string.decode('utf-8')

    def decrypt_json(self, binary_string, key):
        fernet_key = self.generate_fernet_key(key)
        fernet = Fernet(fernet_key)

        try:
            # Convert binary string to bytes
            encrypted_bytes = int(binary_string, 2).to_bytes((len(binary_string) + 7) // 8, byteorder='big')

            # Second layer decryption
            decrypted_bytes_first_layer = fernet.decrypt(encrypted_bytes)
            logging.debug(f"Decrypted bytes first layer: {decrypted_bytes_first_layer}")

            # First layer decryption
            decrypted_bytes = fernet.decrypt(decrypted_bytes_first_layer)
            logging.debug(f"Decrypted bytes: {decrypted_bytes}")

            # JSON to object
            json_data = json.loads(decrypted_bytes.decode("utf-8"))

        except (InvalidToken, ValueError) as e:
            logging.error("Invalid Fernet key, corrupted data, or binary string conversion error")
            return None
        except json.JSONDecodeError:
            logging.error("Corrupted JSON data")
            return None

        return json_data

class Data:
    def __init__(self, database_name, key):
        self.database_name = database_name
        self.database_path = f"./databases/{database_name}"
        if not os.path.exists(self.database_path):
            os.makedirs(self.database_path)

        self.key = key
        self.encryptor = Encrypt()
        self.decryptor = Decrypt()

    def create_collection(self, collection_name):
        collection_path = f"{self.database_path}/{collection_name}.ndb"
        if not os.path.exists(collection_path):
            with open(collection_path, "wb") as collection_file:
                collection_file.write(b"0")

    def read_collection(self, collection_name):
        collection_path = f"{self.database_path}/{collection_name}.ndb"
        if not os.path.exists(collection_path):
            return []

        encrypted_data = self.decryptor.import_from_ndb(collection_path)
        decrypted_data = self.decryptor.decrypt_json(encrypted_data, self.key)
        if (decrypted_data is None) or (decrypted_data == ''):
            return []  # or raise an exception, depending on your requirements
        return decrypted_data

    def write_collection(self, collection_name, data):
        collection_path = f"{self.database_path}/{collection_name}.ndb"
        encrypted_data = self.encryptor.encrypt_json(data, self.key)
        self.encryptor.export_to_ndb(encrypted_data, collection_path)

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