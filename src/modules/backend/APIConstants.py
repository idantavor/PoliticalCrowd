from enum import Enum

USER_TOKEN = "userToken"
BIRTH_YEAR = "birthYear"

class Response(Enum):
    CODE_REQUEST_FAILED = 304
    CODE_TOKEN_NOT_FOUND = 404
    CODE_SUCCESS = 200