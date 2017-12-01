from py2neo.ogm import *

from src.modules.dal.graphObjects.ElectedOfficial import ElectedOfficials
from src.modules.dal.graphObjects.Law import Law
from src.modules.dal.graphObjects.Party import Party


class User(GraphObject):
    __primarykey__ = "token"

    token = Property()
    job = Property(key="job")
    birthYear = Property(key="birthYear")
    residency = Property(key="residency")
    involvmentLevel = Property(key="involvmentLevel")

    associate_party = RelatedTo(Party)
    voted_for = RelatedTo(Law)
    voted_against = RelatedTo(Law)
    member_follows = RelatedTo(ElectedOfficials)

