#      
#
#                                                              
#   ,------.              ,--. ,-----. ,--.  ,--.,------.  ,-----.   
#   |  .--. ',--. ,--.    |  |'  .-.  '|  ,'.|  ||  .-.  \ |  |) /_  
#   |  '--' | \  '  /,--. |  ||  | |  ||  |' '  ||  |  \  :|  .-.  \ 
#   |  | --'   \   ' |  '-'  /'  '-'  '|  | `   ||  '--'  /|  '--' / 
#   `--'     .-'  /   `-----'  `-----' `--'  `--'`-------' `------'  
#            `---'                                                   
#   
#                 made with <3 by tago | version 1.6
#
#           learn more at https://github.com/tagoWorks/pyjondb
#



import json
import os
import base64
import datetime
import uuid
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken

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
        binary_string = '\0' + binary_string
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
            encrypted_bytes = int(binary_string[1:], 2).to_bytes((len(binary_string[1:]) + 7) // 8, byteorder='big')
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

class init:
    def __init__(self, database_name, key, auth, debug=False, absolute=False):
        """
        Initializes a new instance of the `init` class.

        Args:
            database_name (str): The name of the database.
            key (str): The encryption key for the database.
            auth (Auth): The authentication object for the database.
            debug (bool, optional): Whether to enable debug logging. Defaults to False.
            absolute (bool, optional): Whether to use an absolute path for the database file. Defaults to False.

        Raises:
            PermissionError: If authentication fails.

        """
        self.debug = debug
        self.absolute = absolute
        if absolute:
            self.database_path = f"{database_name}.ndb"
        else:
            self.database_path = f"./databases/{database_name}.ndb"
            if not os.path.exists("./databases"):
                os.makedirs("./databases")
        self.database_name = database_name
        self.key = key
        self.encryptor = Encrypt()
        self.decryptor = Decrypt()
        self.auth = auth
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    def create(self, session_id):
        """
        Creates a new database if it doesn't already exist.

        Parameters:
            session_id (str): The ID of the session.


        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        if not os.path.exists(self.database_path):
            metadata = {
                'id': str(uuid.uuid4()),
                'database': self.database_name,
                'creation_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'collections': {}
            }
            self.write(metadata)
            print(f"Database {self.database_name} created with metadata: {metadata}")
        else:
            print(f"Database {self.database_name} already exists.")
    
    def read(self, session_id):
        """
        Reads the contents of the database and returns the decrypted data.

        Args:
            session_id (str): The ID of the session.

            FileNotFoundError: If the database does not exist.

        Returns:
            dict: The decrypted data from the database. If the decrypted data is None, an empty dictionary is returned.
        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(f'Database {self.database_name} does not exist. Create it using create()')
        encrypted_data = self.decryptor.import_from_ndb(self.database_path)
        decrypted_data = self.decryptor.decrypt_json(encrypted_data, self.key)
        if decrypted_data is None:
            return {}
        return decrypted_data
    
    def write(self, data):
        """
        Writes the data to the database.

        Args:
            data (dict): The data to be written to the database.

        """
        encrypted_data = self.encryptor.encryptpydb(data, self.key)
        self.encryptor.exportdb(encrypted_data, self.database_path)
    
    def create_collection(self, collection_name, session_id):
        """
        Creates a new collection in the database.

        Args:
            collection_name (str): The name of the collection.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        if not self.auth.authorize(session_id, 'admin'):
            raise PermissionError("Authorization failed")
        database = self.read(session_id)
        if 'collections' not in database:
            database['collections'] = {}
        if collection_name not in database['collections']:
            database['collections'][collection_name] = {}
            self.write(database)
    
    def read_collection(self, collection_name, session_id):
        """
        Reads the contents of a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            session_id (str): The ID of the session.

        Returns:
            list: The contents of the collection.
        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database or collection_name not in database['collections']:
            return []
        return list(database['collections'][collection_name].values())
    
    def write_collection(self, collection_name, data, session_id):
        """
        Writes data to a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            data (list): The data to be written to the collection.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database:
            database['collections'] = {}
        if collection_name not in database['collections']:
            database['collections'][collection_name] = {}
        for document in data:
            document_id = str(document.get('_id', uuid.uuid4()))
            database['collections'][collection_name][document_id] = document
        self.write(database)
    
    def add_document(self, collection_name, document, session_id):
        """
        Adds a document to a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            document (dict): The document to be added.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database or collection_name not in database['collections']:
            return
        document['_id'] = str(uuid.uuid4())
        self.write_collection(collection_name, [document], session_id)
    
    def find_document(self, collection_name, query, session_id):
        """
        Finds documents in a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to be used for finding documents.
            session_id (str): The ID of the session.

        Returns:
            list: The documents that match the query.
        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        collection = self.read_collection(collection_name, session_id)
        return [document for document in collection if self.query(document, query)]
    
    def query(self, document, query):
        """
        Performs a query on a document.

        Args:
            document (dict): The document to be queried.
            query (dict): The query to be performed.

        Returns:
            bool: True if the query matches the document, False otherwise.
        """
        for field, value in query.items():
            if field == "$and":
                if not all(self.query(document, sub_query) for sub_query in value):
                    return False
            elif field == "$or":
                if not any(self.query(document, sub_query) for sub_query in value):
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
    
    def update_document(self, collection_name, document_id, data, session_id):
        """
        Updates a document in a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            document_id (str): The ID of the document to be updated.
            data (dict): The data to be updated.
            session_id (str): The ID of the session.


        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database or collection_name not in database['collections']:
            return
        if document_id not in database['collections'][collection_name]:
            return
        database['collections'][collection_name][document_id].update(data)
        self.write(database)
    
    def delete_document(self, collection_name, document_id, session_id):
        """
        Deletes a document from a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            document_id (str): The ID of the document to be deleted.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database or collection_name not in database['collections']:
            return
        if document_id not in database['collections'][collection_name]:
            return
        del database['collections'][collection_name][document_id]
        self.write(database)
    
    def link_collections(self, collection1_name, collection2_name, field1, field2, session_id):
        """
        Links two collections in the database.

        Args:
            collection1_name (str): The name of the first collection.
            collection2_name (str): The name of the second collection.
            field1 (str): The name of the field in the first collection.
            field2 (str): The name of the field in the second collection.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        database = self.read(session_id)
        if 'collections' not in database or collection1_name not in database['collections'] or collection2_name not in database['collections']:
            return

        collection1 = database['collections'][collection1_name]
        collection2 = database['collections'][collection2_name]

        for doc1_id, doc1 in collection1.items():
            if field1 in doc1:
                value = doc1[field1]
                if isinstance(value, list):
                    linked_docs = [collection2.get(v) for v in value if v in collection2]
                    doc1[field2] = linked_docs
                elif value in collection2:
                    doc1[field2] = collection2[value]
        self.write(database)
    
    def create_tree(self, collection_name, root_query, child_collection_name, child_query, session_id):
        """
        Creates a tree structure in the database.

        Args:
            collection_name (str): The name of the collection.
            root_query (dict): The query to be used for finding the root documents.
            child_collection_name (str): The name of the child collection.
            child_query (dict): The query to be used for finding the child documents.
            session_id (str): The ID of the session.

        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        root_documents = self.find_document(collection_name, root_query, session_id)
        for root_document in root_documents:
            child_documents = self.find_document(child_collection_name, child_query, session_id)
            root_document["children"] = child_documents
        self.write(self.read(session_id))
        return root_documents
    
    def aggregate(self, collection_name, pipeline, session_id):
        """
        Aggregates a collection in the database.

        Args:
            collection_name (str): The name of the collection.
            pipeline (list): The aggregation pipeline.
            session_id (str): The ID of the session.

        Returns:
            list: The aggregated collection.
        """
        if not self.auth.is_authenticated(session_id):
            raise PermissionError("Authentication failed")
        collection = self.read_collection(collection_name, session_id)

        for stage in pipeline:
            for op, expression in stage.items():
                if op == "$match":
                    collection = [doc for doc in collection if self.query(doc, expression)]
                elif op == "$group":
                    grouped_collection = {}
                    for doc in collection:
                        key = tuple(doc[field] for field in expression["_id"].keys())
                        if key not in grouped_collection:
                            grouped_collection[key] = {k: 0 for k in expression.keys() if k != "_id"}
                            grouped_collection[key]["_id"] = {k: doc[k] for k in expression["_id"].keys()}
                        for field, aggregate_op in expression.items():
                            if field != "_id":
                                if aggregate_op == "$sum":
                                    grouped_collection[key][field] += 1
                    collection = list(grouped_collection.values())
        return collection