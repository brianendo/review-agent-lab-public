"""User service backed by a database, with a read-through cache."""


class UserService:
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def get_user(self, user_id):
        if user_id not in self._cache:
            self._cache[user_id] = self.db.fetch_user(user_id)
        return self._cache[user_id]

    def update_email(self, user_id, email):
        """Update the user's email address."""
        self.db.update_user(user_id, {"email": email})
