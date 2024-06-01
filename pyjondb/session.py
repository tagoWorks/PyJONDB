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
#                 made with <3 by tago | version 2.0
#
#           learn more at https://github.com/tagoWorks/pyjondb
#





import hashlib
import os
import json
import uuid
import datetime

databasepath = None

class start:
    def __init__(self, user_file='users.json', work_in_db_dir=True, session_timeout=3600):
        """
        Initializes a new instance for the database handling.

        Args:
            user_file (str, optional): The path to the user file. Defaults to 'users.json'.
            work_in_db_dir (bool, optional): Whether to work in the databases directory for the user data. Defaults to 'True'
            session_timeout (int, optional): The session timeout in seconds. Defaults to 3600.
        """
        global databasepath
        self.user_file = user_file
        self.work_in_db_dir = work_in_db_dir
        self.users = self.load_users()
        self.sessions = {}
        self.absolute = databasepath
        self.session_timeout = session_timeout

    def load_users(self):
        """
        Loads the users from the user file if it exists.

        Returns:
            dict: A dictionary containing the users loaded from the user file.
                  If the user file does not exist, an empty dictionary is returned.
        """
        user_file_path = self.get_user_file_path()
        if os.path.exists(user_file_path):
            with open(user_file_path, 'r') as f:
                return json.load(f)
        return {}

    def save_users(self):
        """
        Saves the current users to the user file.
        """
        user_file_path = self.get_user_file_path()
        if not os.path.exists(os.path.dirname(user_file_path)):
            if os.path.dirname(user_file_path) == "":
                with open(user_file_path, 'w') as f:
                    json.dump(self.users, f)
                return
            os.makedirs(os.path.dirname(user_file_path))
        with open(user_file_path, 'w') as f:
            json.dump(self.users, f)

    def get_user_file_path(self):
        """
        Determines the correct file path for storing or loading users.

        Returns:
            str: The file path to be used for storing or loading users.
        """
        if self.work_in_db_dir:
            return os.path.join("databases", self.user_file)
        return self.user_file

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