from pyjondb import database
from pyjondb import session

# Initialize authentication
auth = session.start(work_in_db_dir=False)
auth.create_user('admin', 'adminpass', roles=['admin'])

# Authenticate and get a session ID
session_id = auth.authenticate('admin', 'adminpass')
if not session_id:
    raise PermissionError("Authentication failed")

# Initialize the database
db = database.init("database", "mydatabasekey", auth)

# Create the database
# Note: you should only create the database if it doesn't already exist
db.create(session_id)

# Create a collection
db.create_collection("users", session_id)

# Add documents to the collection
document1 = {"_id": 1, "name": "John", "age": 30}
document2 = {"_id": 2, "name": "Jane", "age": 25}
db.add_document("users", document1, session_id)
db.add_document("users", document2, session_id)

# Read the collection
print("Reading collection 'users':")
print(db.read_collection("users", session_id))

# Find documents matching a query
query = {"age": 30}
print("Finding documents in 'users' collection with age 30:")
print(db.find_document("users", query, session_id))

# Update a document
update_data = {"age": 35}
print("Updating document in 'users' collection:")
db.update_document("users", 1, update_data, session_id)
print(db.read_collection("users", session_id))

# Delete a document
print("Deleting document from 'users' collection:")
db.delete_document("users", 2, session_id)
print(db.read_collection("users", session_id))

# Link collections
print("Linking collections:") 
db.link_collections("users", "orders", "user_id", "order_id", session_id)

# Create tree structure
print("Creating tree structure:")
root_query = {"type": "person"}
child_query = {"age": {"$gt": 18}}
print(db.create_tree("people", root_query, "children", child_query, session_id))

# Aggregate collection
print("Aggregating collection:")
pipeline = [
    {"$match": {"age": {"$gt": 18}}},
    {"$group": {"_id": {"age": "$age"}, "$sum": {"count": 1}}}
]
print(db.aggregate("users", pipeline, session_id))