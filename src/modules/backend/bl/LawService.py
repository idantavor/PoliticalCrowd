from flask import json
from py2neo import Graph

from src.modules.dal.relations.Relations import ELECTED_VOTED_FOR, ELECTED_VOTED_AGAINST, ELECTED_MISSING, ELECTED_ABSTAINED
from src.modules.backend.app.WebAPI import app
from src.modules.backend.bl.UserService import isUserExist
from src.modules.backend.common import CommonUtils
from src.modules.dal.graphObjects.graphObjects import User, Law, ElectedOfficial, Vote, Party, Tag
import itertools
from operator import itemgetter

from src.modules.dal.relations.Relations import *

logger = app.logger


def submitVoteAndTags(graph, law_name, tags, user_id, vote):
    user = User.safeSelect(graph=graph, token=user_id)
    if vote is None:
        raise Exception("empty vote")
    if vote is VOTED_FOR:
        user.voteLaw(graph=graph, law_name=law_name, is_upvote=True)
        logger.debug("[" + str(user_id) + "] voted for " + law_name)
    elif vote is VOTED_AGAINST:
        user.voteLaw(graph=graph, law_name=law_name, is_upvote=False)
        logger.debug("[" + str(user_id) + "] voted against " + law_name)
    else:
        raise Exception("ileagal vote type")
    if tags is not None and tags is not []:
        user.tagLaw(graph=graph, law_name=law_name, tags_names=tags)
        logger.debug("[" + str(user_id) + "] tagged law [" + law_name + "] as " + str(tags))
        user.updateRankIfNeeded()
        logger.debug("[" + str(user_id) + "] rank updated")

def getNewLaws(graph, user_id):
    if isUserExist(graph, user_id):
        data = json.load(open('new_laws.json'))
        return len(data), data
    else:
        raise Exception("ileagal operation")


def getAllElectedVotedInLaw(graph, law):
    curr_vote = getLatestVoteForLaw(graph=graph, law=law)
    query = f"MATCH (e:{ElectedOfficial.__name__}) MATCH (v:{Vote.__name__}) " \
            f"WHERE v.raw_title='{curr_vote.raw_title}' AND " \
            f"((v)-[:{ELECTED_VOTED_FOR}]->(e) OR (v)-[:{ELECTED_VOTED_AGAINST}]->(e) OR (v)-[:{ELECTED_ABSTAINED}]->(e))" \
            f"RETURN e"
    data = graph.run(query).data()
    electors = []
    for e in data:
        electors.append(ElectedOfficial.wrap(e['e']))

    return electors


def getLatestVoteForLaw(graph, law):
    query = f"MATCH (v:{Vote.__name__}) MATCH (l:{Law.__name__}) WHERE l.name='{law.name}' AND (v)-[:{LAW}]->(l) " \
            f"RETURN v " \
            f"ORDER BY v.timestamp " \
            f"LIMIT 1"
    logger.debug(f"Query is: {query}")
    data = graph.run(query).data()[0]
    logger.debug(f"data returned: {data['v']}")
    return Vote.wrap(data['v'])


def getAllElectedInPartyVotedInLaw(graph, law, party):
    curr_vote = getLatestVoteForLaw(graph=graph, law=law)
    query = f"MATCH (e:{ElectedOfficial.__name__}) MATCH (v:{Vote.__name__}) MATCH (p:{Party.__name__} " \
            f"WHERE v.raw_title='{curr_vote.raw_title}' AND p.name='{party.name}' AND (e)-[:{MEMBER_OF_PARTY}]->(p) AND " \
            f"((v)-[:{ELECTED_VOTED_FOR}]->(e) OR (v)-[:{ELECTED_VOTED_AGAINST}]->(e) OR (v)-[:{ELECTED_ABSTAINED}]->(e)) " \
            f"RETURN e"
    data = graph.run(query).data()
    electors = []
    for e in data:
        electors.append(ElectedOfficial.wrap(e['e']))

    return electors


def getAllElectedInPartyMissingFromLaw(graph, law, party):
    curr_vote = getLatestVoteForLaw(graph=graph, law=law)
    query = f"MATCH (e:{ElectedOfficial.__name__}) MATCH (p:{Party.__name__}) MATCH (v:{Vote.__name__}) " \
            f"WHERE v.raw_title='{curr_vote.raw_title}' " \
            f"AND p.name='{party.name}' " \
            f"AND (e)-[:{MEMBER_OF_PARTY}]->(p) " \
            f"AND (v)-[:{ELECTED_MISSING}]->(e) " \
            f"RETURN e"
    data = graph.run(query).data()
    electors = []
    for e in data:
        electors.append(ElectedOfficial.wrap(e['e']))

    return electors


def getNumOfLawsByTag(graph, tag, num_of_laws):
    tag_query = "" if tag is None else f"MATCH (t:{Tag.__name__}) WHERE t.name='{tag.name}' AND (l)-[:{TAGGED_AS}]->(t)"
    query = f"MATCH (l:{Law.__name__}) {tag_query} " \
                     f"RETURN l " \
                     f"ORDER BY l.timestamp " \
                     f"LIMIT {num_of_laws}"

    logger.debug(f"query is: {query}")
    data = graph.run(query).data()
    laws = []
    for law in data:
        laws.append(Law.wrap(law['l']))

    return laws


def getLawsByDateInterval(graph, start_date, end_date):
    law_set = Law.select(graph)\
        .where("{}<= _.timestamp <={}".format(start_date, end_date))
    res = {}
    for law in law_set:
        res[law.name] = law.__dict__
    return res


def countPartyVotes(data):
    res = {}
    for selection in data:
        if res[selection["p.name"]] is None:
            res[selection["p.name"]]= {"count" : 1,
                                       "elected_officials" : [selection["e"].properties]}
        else:
            res[selection["p.name"]] = {"count" : res[selection["p.name"]]["count"] +1,
                                        "elected_officials": res[selection["p.name"]]["elected_officials"].append(selection["e"].properties)}
    return res

def calculateStats(voted_for, voted_against, missing, abstained):
    res = {}
    for party, votes in voted_for.items():
        res[party] = {"for" : votes}

    for party, votes in voted_against.items():
        res[party]["against"] = votes

    for party, votes in missing.items():
        res[party]["missing"] = votes

    for party, votes in abstained.items():
        res[party]["abstained"] = votes

    return res

def createStatsResponse(user_party, user_vote, votes):
    res = {}
    for party_name, party_vote in votes.items():
        total_votes = sum(x["count"] for x in party_vote.values())
        voted_like_user = party_vote[user_vote]["count"]
        res[party_name] = {"match": (voted_like_user / total_votes),
                           "is_users_party": True if user_party == party_name else False,
                           "elected_voted_for": party_vote["elected_officials"]}
    return res


def getElectedOfficialLawStats(graph, law_name, user_vote, user_id):

    query = "MATCH(l:Law) MATCH(v:Vote) MATCH(e:ElectedOfficial) MATCH(p:Party)" \
            " WHERE (v)-[:LAW]->(l) AND (v)-[:{}]->(e) AND " \
            "(e)-[:MEMBER_OF_PARTY]->(p) AND " \
            "l.name = '{}' return e, p.name"

    voted_for = graph.run(query.format(ELECTED_VOTED_FOR,law_name)).data()
    voted_against = graph.run(query.format(ELECTED_VOTED_AGAINST, law_name)).data()
    missing = graph.run(query.format(ELECTED_MISSING, law_name)).data()
    abstained = graph.run(query.format(ELECTED_ABSTAINED, law_name)).data()

    voted_for = countPartyVotes(voted_for)
    voted_against = countPartyVotes(voted_against)
    missing = countPartyVotes(missing)
    abstained = countPartyVotes(abstained)

    votes = calculateStats(voted_for, voted_against, missing, abstained)

    user = User.safeSelect(graph = graph, token=user_id)
    user_party = list(user.associate_party)[0].name

    res = createStatsResponse(user_party, user_vote, votes)

    return res



