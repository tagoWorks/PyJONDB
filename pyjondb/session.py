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





import hashlib
import os
import json
import uuid
import datetime

class start:
    def __init__(self, user_file='users.json', absolute=False,  session_timeout=3600):
        """
        Initializes a new instance for the database handling.

        Args:
            user_file (str, optional): The path to the user file. Defaults to 'users.json'.
            absolute (bool, optional): Whether to use an absolute path for the user file. Defaults to False.
            session_timeout (int, optional): The session timeout in seconds. Defaults to 3600.
        """
        self.user_file = user_file
        self.users = self.load_users()
        self.absolute = absolute
        self.sessions = {}
        self.session_timeout = session_timeout
    def load_users(self):
        """
        Loads the users from the user file if it exists.

        Returns:
            dict: A dictionary containing the users loaded from the user file.
                  If the user file does not exist, an empty dictionary is returned.
        """
        if os.path.exists(self.user_file):
            with open(self.user_file, 'r') as f:
                return json.load(f)
        return {}
    def save_users(self):
        if self.absolute == True:
            with open(self.user_file, 'w') as f:
                json.dump(self.users, f)
        else:
            if not os.path.exists("./databases"):
                os.makedirs("./databases")
            with open("./databases/" + self.user_file, 'w') as f:
                json.dump(self.users, f)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    def create_user(self, username, password, roles=None):
        """
        Creates a new user with the given username, password, and optional roles.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.
            roles (list, optional): The roles assigned to the user. Defaults to None.

        Raises:
            ValueError: If a user with the same username already exists.

        Returns:
            None
        """
        if username in self.users:
            raise ValueError("User already exists")
        hashed_password = self.hash_password(password)
        self.users[username] = {
            'password': hashed_password,
            'roles': roles or []
        }
        self.save_users()
    def authenticate(self, username, password):
        """
        Authenticates a user with the given username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            str or None: The session ID if authentication is successful, None otherwise.
        """
        user = self.users.get(username)
        if not user or user['password'] != self.hash_password(password):
            return None
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'username': username,
            'roles': user['roles'],
            'created_at': datetime.datetime.now().timestamp()
        }
        return session_id
    def is_authenticated(self, session_id):
        session = self.sessions.get(session_id)
        if not session:
            return False
        if datetime.datetime.now().timestamp() - session['created_at'] > self.session_timeout:
            del self.sessions[session_id]
            return False
        return True
    def authorize(self, session_id, role):
        session = self.sessions.get(session_id)
        if not session:
            return False
        return role in session['roles']