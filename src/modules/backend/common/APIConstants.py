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
JOB_FOR = "job_for"
JOB_AGAINST = "job_against"
RESIDENT_FOR = "resident_for"
RESIDENT_AGAINST = "resident_against"
AGE_FOR = "age_for"
AGE_AGAINST = "age_against"
SAME = "same"
DIFF = "different"
MEMBER_ABSENT = "member_absent"



class InvolvementLevel(Enum):
    LOW = 50
    MEDIUM = 20
    HIGH = 1


class Response(Enum):
    CODE_REQUEST_FAILED = 304
    CODE_TOKEN_NOT_FOUND = 404
    CODE_SUCCESS = 200


class Rank(Enum):
    First = "1"
    Second = "2"
    Fourth = "3"
    Fifth = "4"
    Third = "5"
    Sixth = "6"
    Seventh = "7"


class AgeRange(Enum):
    First = 18
    Second = 21
    Third = 30
    Fourth = 40
    Fifth = 55
