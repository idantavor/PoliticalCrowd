class UserNotFoundException(Exception):
    def __init__(self, user_name):
        Exception.__init__(self)
        self.message = f"user:{user_name} can't be found in db"

    def __str__(self):
        return f"UserNotFoundException! {self.message}"