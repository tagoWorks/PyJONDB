# main.py
from pyjondb.data import data

# Create a new database instance
key = "my_secret_key"
db = data("my_database", key)
# Create a new collection
db.create_collection("users")

# Add a new document to the collection
user = {"name": "John Doe", "email": "john@example.com"}
db.add_document("users", user)

# Find a document in the collection
query = {"field": "email", "value": "john@example.com"}
user_documents = db.find_document("users", query)
print(user_documents)

# Update a document in the collection
new_data = {"name": "Jane Doe"}
db.update_document("users", query, new_data)

# Delete a document from the collection
db.delete_document("users", query)

# Link two collections
db.create_collection("posts")
post = {"title": "My First Post", "content": "This is my first blog post."}
db.add_document("posts", post)
db.link_collections("users", "posts", "name", "author")