import pyjondb

# Initialize the database
db = pyjondb.database("database", "mypassword")

# Create the database
# Note: you should only create the database if it doesnt already exist
db.create()

# Create a collection
db.create_collection("users")

# Add documents to the collection
document1 = {"_id": 1, "name": "John", "age": 30}
document2 = {"_id": 2, "name": "Jane", "age": 25}
db.add_document("users", document1)
db.add_document("users", document2)

# Read the collection
print("Reading collection 'users':")
print(db.read_collection("users"))

# Find documents matching a query
query = {"age": 30}
print("Finding documents in 'users' collection with age 30:")
print(db.find_document("users", query))

# Update a document
update_data = {"age": 35}
print("Updating document in 'users' collection:")
db.update_document("users", 1, update_data)
print(db.read_collection("users"))

# Delete a document
print("Deleting document from 'users' collection:")
db.delete_document("users", 2)
print(db.read_collection("users"))

# Link collections
print("Linking collections:")
db.link_collections("users", "orders", "user_id", "order_id")

# Create tree structure
print("Creating tree structure:")
root_query = {"type": "person"}
child_query = {"age": {"$gt": 18}}
print(db.create_tree("people", root_query, "children", child_query))

# Aggregate collection
print("Aggregating collection:")
pipeline = [
    {"$match": {"age": {"$gt": 18}}},
    {"$group": {"_id": {"age": "$age"}, "$sum": {"count": 1}}}
]
print(db.aggregate("users", pipeline))
