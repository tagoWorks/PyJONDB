import logging
from pyjondb.data import Data

logging.basicConfig(level=logging.DEBUG)

def run_tests():
    database_name = "testdb"
    key = "mysecretkey"
    
    # Initialize the Data class
    db = Data(database_name, key)
    
    # 1. Add documents to a collection
    print("Adding documents...")
    db.add_document("users", {"name": "John", "age": 30})
    db.add_document("users", {"name": "Jane", "age": 25})
    db.add_document("users", {"name": "Doe", "age": 22})

    # 2. Read the entire collection
    print("Reading collection...")
    users = db.read_collection("users")
    print("Users:", users)

    # 3. Find documents in the collection
    print("Finding documents...")
    query = {"name": "John"}
    found_users = db.find_document("users", query)
    print("Found Users:", found_users)

    # 4. Update a document in the collection
    print("Updating document...")
    update_query = {"name": "Doe"}
    new_data = {"age": 23}
    db.update_document("users", update_query, new_data)

    # 5. Read the collection after update
    print("Reading collection after update...")
    users_after_update = db.read_collection("users")
    print("Users after update:", users_after_update)

    # 6. Delete a document from the collection
    print("Deleting document...")
    delete_query = {"name": "Jane"}
    db.delete_document("users", delete_query)

    # 7. Read the collection after deletion
    print("Reading collection after deletion...")
    users_after_deletion = db.read_collection("users")
    print("Users after deletion:", users_after_deletion)

if __name__ == "__main__":
    run_tests()
