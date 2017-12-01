from py2neo.ogm import *

from src.modules.dal.relations.Relations import ASSOCIATE_PARTY


class Party(GraphObject):
    __primarykey__ = "name"

    name = Property()
    agenda = Property()

    user_follows = RelatedFrom("User", ASSOCIATE_PARTY)
    party_member = RelatedFrom("ElectedOfficials", ASSOCIATE_PARTY)
