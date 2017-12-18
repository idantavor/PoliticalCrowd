from py2neo.ogm import *

from src.modules.dal.relations.Relations import *
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

    @classmethod
    def createPartyFromJson(cls, party_json):
        party = cls()
        for attr in [attrib for attrib in dir(party) if "__" not in attrib]:
            if attr in party_json:
                party.__setattr__(attr, party_json[attr])
        return party

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class ElectedOfficial(GraphObject):
    __primarykey__ = "name"
    name = Property()
    active = Property(key="active")
    title = Property()
    img_url = Property()
    is_active = Property()
    homepage_url=Property()
    member_of_party = RelatedTo(Party)
    votes_envolved_in = RelatedFrom("Vote")
    laws_proposed=RelatedFrom("Law")
    @classmethod
    def createElectedOfficial(cls, name, active, title):
        ret = cls()
        ret.name = name
        ret.active = active
        ret.title = title
        return ret

    @classmethod
    def createElectedOfficialFromJson(cls, official_json,party):
        official = cls()
        official.member_of_party.add(party)
        official.name=" ".join((official_json.get('name').split()))
        official.title=official_json.get('title')
        official.img_url=official_json.get('img_url')
        official.is_active = official_json.get('is_active')
        official.homepage_url=official_json.get('homepage_url')
        return official

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
    votes=RelatedFrom("Vote")
    proposed_by = RelatedTo(ElectedOfficial)
    #tags = RelatedTo(Tag)

    users_taged = RelatedFrom("User", TAGGED_LAW)

    #proposed_by = RelatedTo(ElectedOfficial)

    @classmethod
    def createLaw(cls, name, timestamp, status, description, link):
        law = cls()
        law.name = name
        law.timestamp = timestamp
        law.status = status
        law.description = description
        law.link = link
#        law.tags_votes = {} # TagName : {class votes-> upvotes, downvotes}
        return law


    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()

class Vote(GraphObject):
    __primary__ = "raw_title"
    raw_title=Property()
    type=Property()
    date=Property()
    url = Property()
    vote_num = Property()
    law = RelatedTo(Law)
    meeting_num = Property()
    elected_voted_for = RelatedTo(ElectedOfficial)
    elected_voted_against = RelatedTo(ElectedOfficial)
    elected_abstained = RelatedTo(ElectedOfficial)
    elected_missing = RelatedTo(ElectedOfficial)
    user_voted_for = RelatedFrom("User", VOTED_FOR)
    user_voted_against = RelatedFrom("User", VOTED_AGAINST)

    @classmethod
    def createVoteFromJson(cls, vote_json,law,vote_details_json=None,graph=None):
        vote = cls()
        for attr in [attrib for attrib in dir(vote) if "__" not in attrib]:
            if attr in vote_json:
                vote.__setattr__(attr, vote_json[attr])
        vote.law.add(law)
        if vote_details_json is not None:
            if graph is None:
                raise Exception("pass a graph object in order to retreive the Elected officials")
            for member_name in vote_details_json['FOR']:
                member=ElectedOfficial.select(graph,str(member_name)).first()
                if member is None:
                    raise Exception("fail to retrieve ElectedOfficial {} from db".format(member_name))
                vote.elected_voted_for.add(member)
            for member_name in vote_details_json['ABSTAINED']:
                member = ElectedOfficial.select(graph, member_name).first()
                if member is None:
                    raise Exception("fail to retrieve ElectedOfficial {} from db".format(member_name))
                vote.elected_abstained.add(member)
            for member_name in vote_details_json['DIDNT_VOTE']:
                member = ElectedOfficial.select(graph, member_name).first()
                if member is None:
                    raise Exception("fail to retrieve ElectedOfficial {} from db".format(member_name))
                vote.elected_missing.add(member)
            for member_name in vote_details_json['AGAINST']:
                member = ElectedOfficial.select(graph, member_name).first()
                if member is None:
                    raise Exception("fail to retrieve ElectedOfficial {} from db".format(member_name))
                vote.elected_voted_against.add(member)
        return vote

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
               pass



    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()



