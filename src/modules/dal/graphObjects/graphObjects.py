from py2neo.ogm import *

from src.modules.dal.relations.Relations import *
from src.modules.backend.common.APIConstants import BLANK_TAG
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

    @staticmethod
    def safeSelect(graph, name):
        try:
            party = Party.select(graph=graph, primary_value=name).first()
        except:
            raise Exception(f"No party exist with name:{name}")

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

    laws_proposed=RelatedFrom("Law",PROPOSED_BY)
    voted_for= RelatedFrom("Vote",ELECTED_VOTED_FOR)
    voted_against = RelatedFrom("Vote",ELECTED_VOTED_AGAINST)
    voted_abstained = RelatedFrom("Vote",ELECTED_ABSTAINED)
    vote_missing = RelatedFrom("Vote",ELECTED_MISSING)

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

    @staticmethod
    def safeSelect(graph, name):
        try:
            elected = ElectedOfficial.select(graph=graph, primary_value=name).first()
        except:
            raise Exception(f"No elected official exists with name:{name}")

        return elected

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()



class Tag(GraphObject):
    __primarykey__ = "name"

    name = Property()
    laws = RelatedFrom("Law", TAGGED_AS)

    @staticmethod
    def safeSelect(graph, tag_name):
        try:
            tag = Tag.select(graph=graph, primary_value=tag_name).first()
        except:
            raise Exception(f"No tag exists with name:{name}")

        return tag


class Law(GraphObject):
    __primarykey__ = "name"
    name = Property()
    timestamp = Property(key="timestamp")
    status = Property(key="status")
    description = Property()
    link = Property()
    tags_votes = Property()

    tagged_as = RelatedTo(Tag)
    proposed_by = RelatedTo(ElectedOfficial)

    elected_officials_votes = RelatedFrom("Vote", LAW)
    users_voted_for = RelatedFrom("User", VOTED_FOR)
    users_voted_againts = RelatedFrom("User", VOTED_AGAINST)
    users_taged = RelatedFrom("User", TAGGED_LAW)


    @classmethod
    def createLaw(cls, name, timestamp, status, description, link):
        law = cls()
        law.name = name
        law.timestamp = timestamp
        law.status = status
        law.description = description
        law.link = link
        law.tags_votes = {}  # {TagName : num_of_upvotes}
        return law

    @staticmethod
    def safeSelect(graph, name):
        try:
            law = Law.select(graph=graph, primary_value=name).first()
        except:
            raise Exception(f"No law by name:{name}")

        return law

    def tagLawByName(self, graph, tag_name):
        tagNode = Tag.safeSelect(graph=graph, tag_name=tag_name)
        if tag_name in self.tags_votes:
            self.tags_votes[tag_name] += 1
        else:
            self.tagged_as.add(tagNode)
            self.tags_votes[tag_name] = 1

        graph.begin(autocommit=True)
        graph.push(self)

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class Vote(GraphObject):
    __primary__ = "raw_title"
    raw_title=Property()
    type=Property()
    date=Property()
    url = Property()
    vote_num = Property()
    meeting_num = Property()

    law = RelatedTo(Law)
    elected_voted_for = RelatedTo(ElectedOfficial)
    elected_voted_against = RelatedTo(ElectedOfficial)
    elected_abstained = RelatedTo(ElectedOfficial)
    elected_missing = RelatedTo(ElectedOfficial)

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

    @staticmethod
    def safeSelect(graph, raw_title):
        try:
            vote = Vote.select(graph=graph, primary_value=raw_title).first()
        except:
            raise Exception(f"No vote exists with raw titile:{raw_title}")

        return vote


class JobCategory(GraphObject):
    __primarykey__ = "name"

    name = Property()

    users = RelatedFrom("User", WORK_AT)

    @classmethod
    def createJobCategory(cls, graph, job_name):
        job = cls()
        job.name = job_name
        graph.begin(autocommit=True)
        graph.push(job)

    @staticmethod
    def safeSelect(graph, job_name):
        try:
            job = JobCategory.select(graph=graph, primary_value=job_name).first()
        except:
            raise Exception(f"No job exist with title:{job_name}")

        return job


class Residency(GraphObject):
    __primarykey__ = "name"

    name = Property()

    users = RelatedFrom("User", RESIDING)

    @classmethod
    def createResidency(cls, graph, city_name):
        residency = cls()
        residency.name = city_name
        graph.begin(autocommit=True)
        graph.push(residency)

    @staticmethod
    def safeSelect(graph, name):
        try:
            city = Residency.select(graph=graph, primary_value=name).first()
        except:
            raise Exception(f"No city exist with name:{name}")

        return city


class User(GraphObject):
    __primarykey__ = "token"

    token = Property()
    birth_year = Property(key="birthYear")
    involvment_level = Property(key="involvmentLevel")

    residing = RelatedTo(Residency)
    work_at = RelatedTo(JobCategory)
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
        user.associate_party.add(Party.safeSelect(graph=graph, name=party))
        user.work_at.add(JobCategory.safeSelect(graph=graph, job_name=job))
        user.residing.add(Residency.safeSelect(graph=graph, name=residancy))
        trans = graph.begin()
        graph.push(user)
        trans.commit()
        return user

    @staticmethod
    def userExists(graph, token):
        try:
            user = User.select(graph=graph, primary_value=token).first()
            return True
        except:
            return False

    @staticmethod
    def safeSelect(graph, token):
        try:
            user = User.select(graph=graph, primary_value=token).first()
        except:
            raise Exception(f"No user exist with token:{token}")

        return user

    def changeInvlovmentLevel(self, graph, involvment_level):
        self.involvment_level = involvment_level
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def changeJobField(self, graph, job):
        self.job_category.clear()
        self.job_category = JobCategory.safeSelect(graph=graph, job_name=job)
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def changeResidency(self, graph, city):
        self.residency.clear()
        self.residency = Residency.safeSelect(graph=graph, name=city)
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def changeAssociateParty(self, graph, party):
        self.residency.clear()
        self.associate_party = Party.safeSelect(graph=graph, name=party)
        graph.begin(autocommit=True)
        graph.push(self)
        return True

    def voteLaw(self, graph, law_name, is_upvote=True):
        law = Law.safeSelect(graph=graph, name=law_name)
        if is_upvote:
            if law in self.voted_against:
                self.voted_against.remove(law)

            self.voted_for.add(law)
        else:
            if law in self.voted_for:
                self.voted_for.remove(law)

            self.voted_against.add(law)
        graph.begin(autocommit=True)
        graph.push(self)

    def tagLaw(self, graph, law_name, tags_names):
        law = Law.safeSelect(graph=graph, name=law_name)
        for tag_name in tags_names:
            if tag_name == BLANK_TAG:
               continue
            law.tagLawByName(graph=graph, tag_name=tag_name)
        self.laws_tagged.add(law)
        graph.begin(autocommit=True)
        graph.push(self)


    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()



