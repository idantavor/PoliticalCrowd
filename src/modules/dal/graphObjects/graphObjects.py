from py2neo.ogm import *

from modules.dal.relations.Relations import VOTED_FOR, VOTED_AGAINST, ELECTED_VOTED_FOR_FIRST, ELECTED_VOTED_FOR_SECOND, \
    ELECTED_VOTED_FOR_THIRD, ELECTED_VOTED_AGAINST_FIRST, ELECTED_VOTED_AGAINST_SECOND, ELECTED_VOTED_AGAINST_THIRD, \
    ELECTED_ABSTAINED_FIRST, ELECTED_ABSTAINED_SECOND, ELECTED_ABSTAINED_THIRD, ELECTED_MISSING_FIRST, \
    ELECTED_MISSING_SECOND, ELECTED_MISSING_THIRD, ASSOCIATE_PARTY, MEMBER_OF_PARTY


# dummy classes because no forward decleration!

class Party:
    def __init__(self):
        pass


class Law:
    def __init__(self):
        pass


class ElectedOfficial:
    def __init__(self):
        pass


# end dummy classes

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
    member_follows = RelatedTo(ElectedOfficial)

    @classmethod
    def createUser(cls, token, job, birthYear, residancy, involvmentLevel):
        ret = cls()
        ret.token = token
        ret.job = job
        ret.birthYear = birthYear
        ret.residency = residancy
        ret.involvmentLevel = involvmentLevel
        return ret

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class Law(GraphObject):
    __primarykey__ = "name"

    name = Property()
    timestamp = Property(key="timestamp")
    status = Property(key="status")
    description = Property()
    link = Property()

    user_voted_for = RelatedFrom("User", VOTED_FOR)
    user_voted_against = RelatedFrom("User", VOTED_AGAINST)

    elected_voted_for_first = RelatedTo(ElectedOfficial)
    elected_voted_for_second = RelatedTo(ElectedOfficial)
    elected_voted_for_third = RelatedTo(ElectedOfficial)

    elected_voted_against_first = RelatedTo(ElectedOfficial)
    elected_voted_against_second = RelatedTo(ElectedOfficial)
    elected_voted_against_third = RelatedTo(ElectedOfficial)

    elected_abstained_first = RelatedTo(ElectedOfficial)
    elected_abstained_second = RelatedTo(ElectedOfficial)
    elected_abstained_third = RelatedTo(ElectedOfficial)

    elected_missing_first = RelatedTo(ElectedOfficial)
    elected_missing_second = RelatedTo(ElectedOfficial)
    elected_missing_third = RelatedTo(ElectedOfficial)

    proposed_by = RelatedTo(ElectedOfficial)

    @classmethod
    def createLaw(cls, name, timestamp, status, description, link):
        law = cls()
        law.name = name
        law.timestamp = timestamp
        law.status = status
        law.description = description
        law.link = link
        return law

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class ElectedOfficial(GraphObject):
    __primarykey__ = "name"

    name = Property()
    active = Property(key="active")
    title = Property()

    member_of_party = RelatedTo(Party)

    voted_for_first = RelatedFrom("Law", ELECTED_VOTED_FOR_FIRST)
    voted_for_second = RelatedFrom("Law", ELECTED_VOTED_FOR_SECOND)
    voted_for_third = RelatedFrom("Law", ELECTED_VOTED_FOR_THIRD)

    voted_against_first = RelatedFrom("Law", ELECTED_VOTED_AGAINST_FIRST)
    voted_against_second = RelatedFrom("Law", ELECTED_VOTED_AGAINST_SECOND)
    voted_against_third = RelatedFrom("Law", ELECTED_VOTED_AGAINST_THIRD)

    abstained_first = RelatedFrom("Law", ELECTED_ABSTAINED_FIRST)
    abstained_second = RelatedFrom("Law", ELECTED_ABSTAINED_SECOND)
    abstained_third = RelatedFrom("Law", ELECTED_ABSTAINED_THIRD)

    missing_first = RelatedFrom("Law", ELECTED_MISSING_FIRST)
    missing_second = RelatedFrom("Law", ELECTED_MISSING_SECOND)
    missing_third = RelatedFrom("Law", ELECTED_MISSING_THIRD)

    @classmethod
    def createElectedOfficial(cls, name, active, title):
        ret = cls()
        ret.name = name
        ret.active = active
        ret.title = title
        return ret

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class Party(GraphObject):
    __primarykey__ = "name"

    name = Property()
    agenda = Property()

    user_follows = RelatedFrom("User", ASSOCIATE_PARTY)
    party_members = RelatedFrom("ElectedOfficial", MEMBER_OF_PARTY)

    @classmethod
    def createParty(cls, name, agenda):
        party = cls()
        party.name = name
        party.agenda = agenda
        return party

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()
