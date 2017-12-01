from py2neo.ogm import *





class Law(GraphObject):
    __primarykey__ = "name"


class User(GraphObject):
    __primarykey__ = "token"

    token = Property()
    jobField = Property()
    age = Property()

    party = RelatedFrom(Party, )
    lawsFor = RelatedFrom(Law)
    lawsAgaints = RelatedTo(Law)


