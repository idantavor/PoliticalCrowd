from py2neo.ogm import *

from src.modules.dal.relations.Relations import VOTED_FOR, VOTED_AGAINST, ELECTED_VOTED_FOR_FIRST, \
    ELECTED_VOTED_FOR_SECOND, \
    ELECTED_VOTED_FOR_THIRD, ELECTED_VOTED_AGAINST_FIRST, ELECTED_VOTED_AGAINST_SECOND, ELECTED_VOTED_AGAINST_THIRD, \
    ELECTED_ABSTAINED_FIRST, ELECTED_ABSTAINED_SECOND, ELECTED_ABSTAINED_THIRD, ELECTED_MISSING_FIRST, \
    ELECTED_MISSING_SECOND, ELECTED_MISSING_THIRD, ASSOCIATE_PARTY, MEMBER_OF_PARTY, TAGGED_AS, TAGGED_LAW, WORK_AT, \
    RESIDING
from src.modules.backend.APIConstants import BLANK_TAG
import datetime


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


class Tag(GraphObject):
    __primarykey__ = "name"

    name = Property()
    laws = RelatedFrom("Law", TAGGED_AS)


class Votes(object):
    def __init__(self):
        self._upvotes = 0

    def upvote(self):
        self._upvotes += 1

    def getScore(self):
        return self._upvotes



class Law(GraphObject):
    __primarykey__ = "name"

    name = Property()
    timestamp = Property(key="timestamp")
    status = Property(key="status")
    description = Property()
    link = Property()
    tags_votes = Property()

    tags = RelatedTo(Tag)
    users_taged = RelatedFrom("User", TAGGED_LAW)

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
        law.tags_votes = {} # TagName : {class votes-> upvotes, downvotes}
        return law

    # def tagVote(self, graph, tag_name, is_upvote=True):
    #     if tag_name not in self.tags_votes:
    #         self.tags_votes[tag_name] = Votes()
    #     if is_upvote:
    #         self.tags_votes[tag_name].upvote()
    #     else:
    #         self.tags_votes[tag_name].downvote()
    #     tagNode = Tag.select(graph, primary_value=tag_name)
    #     self.tags.add(tagNode).first()



    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class JobCategory(GraphObject):
    __primarykey__ = "name"

    name = Property()
    users = RelatedFrom("User", WORK_AT)


class Residency(GraphObject):
    __primarykey__ = "name"

    name = Property()
    users = RelatedFrom("User", RESIDING)


class User(GraphObject):
    __primarykey__ = "token"

    token = Property()
    birth_year = Property(key="birthYear")
    involvment_level = Property(key="involvmentLevel")

    residency = RelatedTo(Residency)
    job_category = RelatedTo(JobCategory)
    associate_party = RelatedTo(Party)
    voted_for = RelatedTo(Law)
    voted_against = RelatedTo(Law)
    laws_tagged = RelatedTo(Law)

    @classmethod
    def createUser(cls, graph, token, job, birthYear, residancy, involvmentLevel, party):
        user = cls()
        user.token = token
        user.birth_year = birthYear
        user.involvment_level = involvmentLevel
        user.associate_party = Party.select(graph, primary_value=party).first()
        user.job_category = JobCategory.select(graph, primary_value=job).first()
        user.residency = Residency.select(graph, primary_value=residancy).first()
        trans = graph.begin()
        graph.push(user)
        trans.commit()
        return user

    def getUserAge(self):
        curr_year = datetime.datetime.now().year
        return curr_year - int(self.birth_year)

    def changeInvlovmentLevel(self, graph, involvment_level):
        self.involvment_level = involvment_level
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def changeJobField(self, graph, job):
        self.job_category = job
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def changeAssociateParty(self, graph, party):
        self.associate_party = Party.select(graph=graph, primary_value=party).first()
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def voteLaw(self, graph, law_name, is_upvote=True):
        law = Law.select(graph, primary_value=law_name).first()
        if is_upvote:
            self.voted_for.add(law)
        else:
            self.voted_against.add(law)
        graph.begin(autocommit=True)
        graph.push(self)

    def tagLaw(self, graph, law_name, tags_names):
        law = Law.select(graph=graph, primary_value=law_name).first()
        for tag_name in tags_names:
            if tag_name != BLANK_TAG:
                law.    



    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()



