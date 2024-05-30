from pyjondb.data import Data

db = Data("example_db", "your_secret_key")
db.create_collection("users")
db.create_collection("posts")
db.add_document("users", {"name": "John", "age": 30})
db.add_document("posts", {"title": "My Post", "content": "This is my post."})
print(db.read_collection("users"))