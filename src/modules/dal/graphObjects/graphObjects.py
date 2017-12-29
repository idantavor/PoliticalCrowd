from flask import jsonify
from py2neo.ogm import *

from src.modules.backend.common.APIConstants import Rank, InvolvementLevel
from src.modules.dal.relations.Relations import *


def selfUpdateGraph(graph, obj):
    graph.begin(autocommit=True)
    graph.push(obj)


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
            raise Exception("No party exist with name:{}".format(name))

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

        ret.select()

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
            raise Exception("No elected official exists with name:{}".format(name))

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
            raise Exception("No tag exists with name:{}".format(tag_name))

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
    users_tagged = RelatedFrom("User", TAGGED_LAW)


    @classmethod
    def createLaw(cls, name, timestamp, status, description, link):
        law = cls()
        law.name = name
        law.timestamp = timestamp
        law.status = status
        law.description = description
        law.link = link
        law.tags_votes = []  # This list should contain tag GraphObject instead of a dictionary that is not supported
        return law

    @staticmethod
    def safeSelect(graph, name):
        try:
            law = Law.select(graph=graph, primary_value=name).first()
        except:
            raise Exception("No law by name:{}".format(name))

        return law

    def tagLawByName(self, graph, tag_name):
        tagNode = Tag.safeSelect(graph=graph, tag_name=tag_name)
        tags_as_dict = dict(self.tags_votes)
        if tag_name in tags_as_dict:
            tags_as_dict[tag_name] += 1
        else:
            self.tagged_as.add(tagNode)
            tags_as_dict[tag_name] = 1

        self.tags_votes = list(tags_as_dict.items())

        graph.begin(autocommit=True)
        graph.push(self)

    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()


class Vote(GraphObject):
    __primarykey__ = "raw_title"
    raw_title=Property()
    type=Property()
    date=Property()
    timestamp=Property()
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
            raise Exception("No vote exists with raw titile:{}".format(raw_title))

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
            raise Exception("No job exist with title:{}".format(job_name))

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
            raise Exception("No city exist with name:{}".format(name))

        return city


class User(GraphObject):
    __primarykey__ = "token"

    token = Property(key="token")
    birth_year = Property(key="birthYear")
    involvement_level = Property(key="involvmentLevel")
    rank = Property(key="rank")
    score = Property(key="score")

    residing = RelatedTo(Residency)
    work_at = RelatedTo(JobCategory)
    associate_party = RelatedTo(Party)
    voted_for = RelatedTo(Law)
    voted_against = RelatedTo(Law)
    laws_tagged = RelatedTo(Law)

    def __str__(self):
        return jsonify({
            "token": self.token,
            "birth_year" : self.birth_year,
            "involvment_level" : InvolvementLevel(self.involvement_level).value,
            "rank" : Rank(self.rank)
        })

    @classmethod
    def createUser(cls, graph, token, job, birthYear, residancy, involvementLevel, party):
        user = cls()
        user.token = token
        user.rank = Rank.First.value
        user.birth_year = birthYear
        user.involvement_level = involvementLevel
        user.score = 0
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
            raise Exception("No user exist with token:{}".format(token))

        return user

    def changeInvlovmentLevel(self, graph, involvement_level):
        self.involvement_level = involvement_level
        selfUpdateGraph(graph=graph, obj=self)
        return True

    def changeJobField(self, graph, job):
        self.job_category.clear()
        self.job_category = JobCategory.safeSelect(graph=graph, job_name=job)
        selfUpdateGraph(graph=graph, obj=self)
        return True

    def updateRankIfNeeded(self):
        self.score += 1
        if self.score < 15:
            self.rank = Rank.First
        elif self.score < 30:
            self.rank = Rank.Second
        elif self.score < 60:
            self.rank = Rank.Third
        elif self.score < 70:
            self.rank = Rank.Fourth
        elif self.score < 85:
            self.rank = Rank.Fifth
        else:
            self.rank = Rank.Sixth


    def changeResidency(self, graph, city):
        self.residency.clear()
        self.residency = Residency.safeSelect(graph=graph, name=city)
        selfUpdateGraph(graph=graph, obj=self)
        return True

    def changeAssociateParty(self, graph, party):
        self.residency.clear()
        self.associate_party = Party.safeSelect(graph=graph, name=party)
        selfUpdateGraph(graph=graph, obj=self)
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

        self.updateRankIfNeeded(graph)

        selfUpdateGraph(graph=graph, obj=self)

    def tagLaw(self, graph, law_name, tags_names):
        law = Law.safeSelect(graph=graph, name=law_name)
        for tag_name in tags_names:
            law.tagLawByName(graph=graph, tag_name=tag_name)
        self.laws_tagged.add(law)
        selfUpdateGraph(graph=graph, obj=self)


    def __str__(self, *args, **kwargs):
        return self.__ogm__.node.__str__()



