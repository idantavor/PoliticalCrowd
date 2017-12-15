from enum import Enum

USER_TOKEN = "userToken"
BIRTH_YEAR = "birthYear"
JOB = "job"
RESIDANCY = "residancy"
PARTY = "party"
INVOLVEMENT_LEVEL = "involvement_level"
BLANK_TAG = "blankTag"

class InvolvementLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Response(Enum):
    CODE_REQUEST_FAILED = 304
    CODE_TOKEN_NOT_FOUND = 404
    CODE_SUCCESS = 200