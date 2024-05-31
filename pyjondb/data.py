import json
import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken

logging.basicConfig(level=logging.DEBUG)

class Encrypt:
    @staticmethod
    def generate_fernet_key(key):
        return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())

    def encryptpydb(self, json_data, key):
        fernet_key = self.generate_fernet_key(key)
        fernet = Fernet(fernet_key)

        json_bytes = json.dumps(json_data).encode("utf-8")
        encrypted_bytes = fernet.encrypt(json_bytes)
        logging.debug(f"Encrypted bytes: {encrypted_bytes}")

        second_layer_encrypted_bytes = fernet.encrypt(encrypted_bytes)
        logging.debug(f"Second layer encrypted bytes: {second_layer_encrypted_bytes}")

        binary_string = ''.join(format(byte, '08b') for byte in second_layer_encrypted_bytes)
        logging.debug(f"Binary string: {binary_string}")

        return binary_string.encode('utf-8')

    def exportdb(self, binary_string, filename):
        with open(filename, "wb") as f:
            f.write(binary_string)

class Decrypt:
    @staticmethod
    def generate_fernet_key(key):
        return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())

    def import_from_ndb(self, filename):
        with open(filename, "rb") as f:
            binary_string = f.read()
        return binary_string.decode('utf-8')

    def decrypt_json(self, binary_string, key):
        fernet_key = self.generate_fernet_key(key)
        fernet = Fernet(fernet_key)

        try:
            encrypted_bytes = int(binary_string, 2).to_bytes((len(binary_string) + 7) // 8, byteorder='big')
            decrypted_bytes_first_layer = fernet.decrypt(encrypted_bytes)
            logging.debug(f"Decrypted bytes first layer: {decrypted_bytes_first_layer}")

            decrypted_bytes = fernet.decrypt(decrypted_bytes_first_layer)
            logging.debug(f"Decrypted bytes: {decrypted_bytes}")

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
        self.database_path = f"./databases/{database_name}.ndb"
        if not os.path.exists("./databases"):
            os.makedirs("./databases")

        self.key = key
        self.encryptor = Encrypt()
        self.decryptor = Decrypt()

        if not os.path.exists(self.database_path):
            self.write([])

    def read(self):
        encrypted_data = self.decryptor.import_from_ndb(self.database_path)
        decrypted_data = self.decryptor.decrypt_json(encrypted_data, self.key)
        if decrypted_data is None:
            return []
        return decrypted_data

    def write(self, data):
        encrypted_data = self.encryptor.encryptpydb(data, self.key)
        self.encryptor.exportdb(encrypted_data, self.database_path)

    def create_collection(self, collection_name):
        pass

    def read_collection(self, collection_name):
        database = self.read()
        return [document for document in database if document.get("collection") == collection_name]

    def write_collection(self, collection_name, data):
        database = self.read()
        for document in data:
            document["collection"] = collection_name
        database.extend(data)
        self.write(database)

    def add_document(self, collection_name, document):
        document["collection"] = collection_name
        self.write_collection(collection_name, [document])

    def find_document(self, collection_name, query):
        collection = self.read_collection(collection_name)
        return [document for document in collection if self.quary(document, query)]

    def quary(self, document, query):
        for field, value in query.items():
            if field == "$and":
                if not all(self.quary(document, sub_query) for sub_query in value):
                    return False
            elif field == "$or":
                if not any(self.quary(document, sub_query) for sub_query in value):
                    return False
            elif field in document:
                if isinstance(value, dict):
                    for op, sub_value in value.items():
                        if op == "$gt":
                            if not document[field] > sub_value:
                                return False
                        elif op == "$lt":
                            if not document[field] < sub_value:
                                return False
                        elif op == "$gte":
                            if not document[field] >= sub_value:
                                return False
                        elif op == "$lte":
                            if not document[field] <= sub_value:
                                return False
                        elif op == "$eq":
                            if not document[field] == sub_value:
                                return False
                        elif op == "$ne":
                            if not document[field] != sub_value:
                                return False
                else:
                    if document[field] != value:
                        return False
            else:
                return False
        return True

    def update_document(self, collection_name, query, new_data):
        database = self.read()
        for document in database:
            if document.get("collection") == collection_name and self.quary(document, query):
                document.update(new_data)
        self.write(database)

    def delete_document(self, collection_name, query):
        database = self.read()
        database = [document for document in database if not (document.get("collection") == collection_name and self.quary(document, query))]
        self.write(database)

    def link_collections(self, collection1_name, collection2_name, field1, field2):
        database = self.read()
        for document1 in (doc for doc in database if doc.get("collection") == collection1_name):
            if field1 in document1:
                document1[field2] = [document2 for document2 in database if document2.get("collection") == collection2_name and document2[field2] == document1[field1]]
        self.write(database)

    def create_tree(self, collection_name, root_query, child_collection_name, child_query):
        database = self.read()
        root_documents = self.find_document(collection_name, root_query)
        for root_document in root_documents:
            child_documents = self.find_document(child_collection_name, child_query)
            root_document["children"] = child_documents
        self.write(database)
        return root_documents

    def aggregate(self, collection_name, pipeline):
        collection = self.read_collection(collection_name)
        for stage in pipeline:
            for op, expression in stage.items():
                if op == "$match":
                    collection = [doc for doc in collection if self.quary(doc, expression)]
                elif op == "$group":
                    grouped_collection = {}
                    for doc in collection:
                        key = tuple(doc[field] for field in expression["_id"].keys())
                        if key not in grouped_collection:
                            grouped_collection[key] = {k: 0 for k in expression.keys() if k != "_id"}
                            grouped_collection[key]["_id"] = {k: doc[k] for k in expression["_id"].keys()}
                        for field, aggregate_op in expression.items():
                            if field != "_id":
                                if aggregate_op["$sum"] == 1:
                                    grouped_collection[key][field] += 1
                    collection = list(grouped_collection.values())
        return collection