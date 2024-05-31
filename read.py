from pyjondb.data import Data

db = Data("example_db", "your_secret_key")

query = {"age": 30}
matching_documents = db.find_document("users", query)
print("Matching documents:", matching_documents)

# Complex query example
complex_query = {"$or": [{"age": 25}, {"name": "Alice"}]}
complex_matching_documents = db.find_document("users", complex_query)
print("Complex matching documents:", complex_matching_documents)