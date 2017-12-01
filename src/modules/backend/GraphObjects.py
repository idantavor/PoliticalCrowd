from py2neo.ogm import *
from Relations import *

class Party(GraphObject):
    __primarykey__ = "name"


class Law(GraphObject):
    __primarykey__ = "name"


class User(GraphObject):
    __primarykey__ = "token"

    token = Property()
    jobField = Property()
    age = Property()

    party = RelatedFrom(Party, )
    lawsFor = RelatedTo(Law)
    lawsAgaints = RelatedTo(Law)


