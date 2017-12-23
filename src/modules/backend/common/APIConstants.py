from enum import Enum

USER_TOKEN = "user_token"
BIRTH_YEAR = "birth_year"
JOB = "job"
RESIDENCY = "residency"
PARTY = "party"
INVOLVEMENT_LEVEL = "involvement_level"
BLANK_TAG = "blank_tag"
VOTE = "vote"
LAW_NAME = "law_name"

VOTED_FOR = "voted_for"
VOTED_AGAINST = "voted_against"
VOTED_ABSTAINED = "voted_abstained"
VOTED_MISSING = "voted_missing"
TAGS= "tags"
NUM_OF_LAWS_BACKWARDS="num_of_laws_backwards"
ELECTED_OFFICIAL="elected_official"
START_DATE = "start_date"
END_DATE = "end_date"

class InvolvementLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Response(Enum):
    CODE_REQUEST_FAILED = 304
    CODE_TOKEN_NOT_FOUND = 404
    CODE_SUCCESS = 200


class Rank(Enum):
    First = "Tourist"
    Second = "Citizen"
    Third = ""
    Fourth = ""
    Fifth = ""
    Sixth = ""
