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

        # Add a null character at the beginning of the binary string
        binary_string = '\0' + binary_string

        logging.debug(f"Binary string: {binary_string}")

        return binary_string.encode('utf-8')

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
            # Remove the null character from the beginning of the binary string
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

class database:
    def __init__(self, database_name, key, debug=False):
        """
        Initializes a new instance of the Database.

        Parameters:
            - database_name (str): The name of the database.
            - key (str): The encryption key.
            - debug (bool, optional): Whether to enable debug mode. Defaults to False.
        """
        self.database_name = database_name
        self.debug = debug
        self.database_path = f"./databases/{database_name}.ndb"
        if not os.path.exists("./databases"):
            os.makedirs("./databases")
        self.key = key
        self.encryptor = Encrypt()
        self.decryptor = Decrypt()
        if debug == True:
            logging.basicConfig(level=logging.DEBUG)

    def create(self):
        """
        Creates a new database file if it doesn't already exist.

        This function checks if the database file specified by `self.database_path` exists. If it doesn't exist, a new file is created using the `open` function with the 'a' mode. The file is then closed using the `close` method. Finally, a message is printed indicating that the database has been created.

        If the database file already exists, a message is printed indicating that the database already exists.
        """
        if not os.path.exists(self.database_path):
            metadata = {
                'id': str(uuid.uuid4()),
                'database': self.database_name,
                'creation_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            with open(self.database_path, 'w') as f:
                json.dump(metadata, f)

            print(f"Database {self.database_name} created with metadata: {metadata}")
        else:
            print(f"Database {self.database_name} already exists.")

    def read(self):
        """
        Reads the data from the database file and returns the decrypted data.

        This function checks if the database file specified by `self.database_path` exists. If it doesn't exist, a `FileNotFoundError` is raised with a message indicating that the database does not exist and suggesting to create it using the `create` method.

        If the database file exists, the function reads the encrypted data from the file using the `import_from_ndb` method of the `decryptor` object. Then, it decrypts the data using the `decrypt_json` method of the `decryptor` object, passing the encrypted data and the encryption key (`self.key`). If the decryption is successful, the decrypted data is returned. If the decryption fails, an empty list is returned.

        Parameters:
            - self: The instance of the class.

        Returns:
            - The decrypted data from the database file. If the decryption fails or the database file is empty, an empty list is returned.
        """
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(f'Database {self.database_name} does not exist. Create it using create("database_name")')
        encrypted_data = self.decryptor.import_from_ndb(self.database_path)
        decrypted_data = self.decryptor.decrypt_json(encrypted_data, self.key)
        if decrypted_data is None:
            return []
        return decrypted_data
    def write(self, data):
        """
        Encrypts the given data using the encryptor and writes it to the database.

        Parameters:
            - data (Any): The data to be written to the database.
        """
        encrypted_data = self.encryptor.encryptpydb(data, self.key)
        self.encryptor.exportdb(encrypted_data, self.database_path)

    def create_collection(self, collection_name):
        """
        Creates a new collection in the database if it doesn't already exist.

        Parameters:
            - collection_name (str): The name of the collection to be created.

        This function reads the current database using the `read` method. If the `collection_name` is not already in the database, a new collection is created with an empty list as its value. The updated database is then written back to the database using the `write` method.
        """
        database = self.read()
        if collection_name not in database:
            database[collection_name] = []
            self.write(database)
    
    def read_collection(self, collection_name):
        """
        Reads a collection from the database and returns the documents that belong to the specified collection.

        Parameters:
            - collection_name (str): The name of the collection to read.

        Returns:
            - List[Dict[str, Any]]: A list of documents that belong to the specified collection.

        This function reads the entire database using the `read` method and filters the documents based on the `collection` field. It returns a list of documents that have the specified `collection_name`.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> db.read_collection("users")
            [{"name": "John", "age": 30, "collection": "users"}, {"name": "Jane", "age": 25, "collection": "users"}]
        """
        database = self.read()
        return [document for document in database if document.get("collection") == collection_name]

    def write_collection(self, collection_name, data):
        """
        Writes a collection of documents to the database.

        Parameters:
            - collection_name (str): The name of the collection to write the documents to.
            - data (List[Dict[str, Any]]): The list of documents to write.

        This function reads the current database using the `read` method. It then iterates over each document in the `data` list and adds the `collection_name` field to each document. Finally, it extends the database with the new documents and writes the updated database back to the database using the `write` method.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
            >>> db.write_collection("users", data)
        """
        database = self.read()
        for document in data:
            document["collection"] = collection_name
        database.extend(data)
        self.write(database)

    def add_document(self, collection_name, document):
        """
        Adds a document to a collection in the database.

        Parameters:
            - collection_name (str): The name of the collection to add the document to.
            - document (Dict[str, Any]): The document to add to the collection.

        This function adds a document to a collection in the database. It first adds a "collection" field to the document with the value of the `collection_name` parameter. Then, it calls the `write_collection` method to write the document to the database.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> document = {"name": "John", "age": 30}
            >>> db.add_document("users", document)
        """
        document["collection"] = collection_name
        self.write_collection(collection_name, [document])

    def find_document(self, collection_name, query):
        """
        Finds documents in a collection that match the given query.

        Args:
            - collection_name (str): The name of the collection to search in.
            - query (Dict[str, Any]): The query to match against the documents.

        Returns:
            - List[Dict[str, Any]]: A list of documents that match the query.

        This function reads the collection specified by `collection_name` and searches for documents that match the given `query`. It uses the `quary` method to check if a document matches the query. The matching documents are returned as a list.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> query = {"name": "John", "age": 30}
            >>> matching_documents = db.find_document("users", query)
            >>> print(matching_documents)
            [{"name": "John", "age": 30, "collection": "users"}]
        """
        collection = self.read_collection(collection_name)
        return [document for document in collection if self.quary(document, query)]

    def quary(self, document, query):
        """
        Recursively queries a document to determine if it matches a given query.

        Args:
            - document (dict): The document to be queried.
            - query (dict): The query to match against the document.

        Returns:
            - bool: True if the document matches the query, False otherwise.

        This function iterates over each key-value pair in the query dictionary and checks if the document matches the query. It supports the following query operators:
        
        - "$and": Matches if all sub-queries match.
        - "$or": Matches if any sub-query matches.
        - Field: Matches if the field exists in the document and its value matches the query value.
        - Field with dictionary: Matches if the field exists in the document and its value satisfies the specified operator. Supported operators are:
            - "$gt": Greater than.
            - "$lt": Less than.
            - "$gte": Greater than or equal to.
            - "$lte": Less than or equal to.
            - "$eq": Equal to.
            - "$ne": Not equal to.

        If any condition fails, the function immediately returns False. If all conditions pass, the function returns True.

        Example:
            >>> doc = {"name": "John", "age": 30}
            >>> query = {"name": "John", "age": {"$gt": 25}}
            >>> quary(doc, query)
            True
        """
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
        """
        Updates a document in a collection based on a query.

        Args:
            - collection_name (str): The name of the collection to update.
            - query (dict): The query to match against the documents in the collection.
            - new_data (dict): The new data to update the matching document with.

        This function reads the database, iterates over each document in the collection, and checks if the document matches the query. If a matching document is found, it updates the document with the new data provided. Finally, it writes the updated database back to the file.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> query = {"name": "John", "age": 30}
            >>> new_data = {"age": 35}
            >>> db.update_document("users", query, new_data)
            >>> # The document with the name "John" and age 30 in the "users" collection is updated with the new data.
        """
        database = self.read()
        for document in database:
            if document.get("collection") == collection_name and self.quary(document, query):
                document.update(new_data)
        self.write(database)

    def delete_document(self, collection_name, query):
        """
        Deletes a document from the specified collection based on a query.

        Args:
            - collection_name (str): The name of the collection to delete the document from.
            - query (dict): The query to match against the documents in the collection.

        This function reads the database, filters out the documents that match the specified collection name and query,
        and writes the updated database back to the file.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> query = {"name": "John", "age": 30}
            >>> db.delete_document("users", query)
            >>> # The document with the name "John" and age 30 in the "users" collection is deleted.
        """
        database = self.read()
        database = [document for document in database if not (document.get("collection") == collection_name and self.quary(document, query))]
        self.write(database)

    def link_collections(self, collection1_name, collection2_name, field1, field2):
        """
        Links two collections in the database by creating a reference field in one collection to the other collection.

        Parameters:
            - collection1_name (str): The name of the first collection.
            - collection2_name (str): The name of the second collection.
            - field1 (str): The field in the first collection that will be used to create the reference.
            - field2 (str): The field in the second collection that will be referenced by the first collection.

        This function reads the database, iterates over each document in the first collection, and checks if the specified field exists in the document. If the field exists, it searches for documents in the second collection that have the same value in the specified field. The function then creates a reference field in the first collection that points to the matching document in the second collection. Finally, the updated database is written back to the file.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> db.link_collections("users", "orders", "user_id", "order_id")
            >>> # The "user_id" field in each document in the "users" collection is linked to the corresponding "order_id" field in the "orders" collection.
        """
        database = self.read()
        for document1 in (doc for doc in database if doc.get("collection") == collection1_name):
            if field1 in document1:
                document1[field2] = [document2 for document2 in database if document2.get("collection") == collection2_name and document2[field2] == document1[field1]]
        self.write(database)

    def create_tree(self, collection_name, root_query, child_collection_name, child_query):
        """
        Creates a tree structure by linking root documents to their corresponding child documents.

        Args:
            - collection_name (str): The name of the root collection.
            - root_query (dict): The query to find root documents in the root collection.
            - child_collection_name (str): The name of the child collection.
            - child_query (dict): The query to find child documents in the child collection.

        Returns:
            - list: A list of root documents with their corresponding child documents added as "children" field.

        This function reads the database, finds root documents in the specified root collection that match the given root query,
        and for each root document, finds the corresponding child documents in the specified child collection that match the given child query.
        It then adds the child documents as "children" field to each root document. Finally, it writes the updated database and returns the list of root documents.

        Example:
            >>> db = Data("example_db", "example_key")
            >>> root_query = {"type": "person"}
            >>> child_query = {"age": {"$gt": 18}}
            >>> db.create_tree("people", root_query, "children", child_query)
            >>> # The "people" collection is the root collection, and the "children" collection is the child collection.
            >>> # The root documents that match the root query will have their "children" field populated with the corresponding child documents that match the child query.
        """
        database = self.read()
        root_documents = self.find_document(collection_name, root_query)
        for root_document in root_documents:
            child_documents = self.find_document(child_collection_name, child_query)
            root_document["children"] = child_documents
        self.write(database)
        return root_documents

    def aggregate(self, collection_name, pipeline):
        """
        Aggregates the documents in a collection based on the given pipeline.

        Args:
            - collection_name (str): The name of the collection.
            - pipeline (list): The aggregation pipeline consisting of stages.

        Returns:
            - list: The aggregated collection of documents.

        The pipeline consists of stages that perform operations on the documents. The following operations are supported:
            - $match: Filters the documents based on the given expression.
            - $group: Groups the documents based on the specified expression and performs aggregation operations.

        The $match stage filters the documents based on the given expression. The expression is a dictionary where the keys represent the fields to match and the values represent the values to match against.

        The $group stage groups the documents based on the specified expression and performs aggregation operations. The expression is a dictionary where the keys represent the fields to group by and the values represent the aggregation operations to perform. The aggregation operations supported are:
            - $sum: Sums the values of the specified field.

        The aggregated collection is returned as a list of documents.

        Example usage:
        ```
        pipeline = [
            {"$match": {"age": {"$gt": 18}}},
            {"$group": {"_id": {"age": "$age"}, "$sum": {"count": 1}}}
        ]
        aggregated_collection = aggregate("users", pipeline)
        ```
        """
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