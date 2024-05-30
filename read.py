from pyjondb.data import Data as data

# Create a new database instance
key = "testkey123"
db = data("my_database", key)
# Link the collections
db.link_collections("users", "posts", "email", "author")

# Find a document in the collection
query = {"field": "email", "value": "john@example.com"}
user_documents = db.find_document("users", query)
print("User documents found:", user_documents)

# Read and print all documents from the collections
users_collection = db.read_collection("users")
print("All users:", users_collection)

posts_collection = db.read_collection("posts")
print("All posts:", posts_collection)