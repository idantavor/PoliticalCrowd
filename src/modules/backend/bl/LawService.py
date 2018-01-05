from datetime import datetime
import time

import logging
from itertools import islice

from flask import json

from src.modules.backend.common.APIConstants import InvolvementLevel
from src.modules.dal.relations.Relations import ELECTED_VOTED_FOR, ELECTED_VOTED_AGAINST, ELECTED_MISSING, ELECTED_ABSTAINED

from src.modules.backend.bl import UserService
from src.modules.dal.graphObjects.graphObjects import User, Law, ElectedOfficial, Vote, Party, Tag, GeneralInfo

from src.modules.dal.relations.Relations import *

logger = logging.getLogger(__name__)


def getLawTags(graph, law_name):
    law = Law.safeSelect(graph=graph, name=law_name)
    tags = islice(sorted(law.tags_votes, key=lambda tup: tup[1], reverse=True), 2)
    return [tag[0] for tag in tags]


def submitVoteAndTags(graph, law_name, tags, user_id, vote):
    user = User.safeSelect(graph=graph, token=user_id)
    if vote is None:
        raise Exception("empty vote")
    if vote == VOTED_FOR:
        user.voteLaw(graph=graph, law_name=law_name, is_upvote=True)
        logger.debug("[" + str(user_id) + "] voted for " + law_name)
    elif vote == VOTED_AGAINST:
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
    today_timestamp = time.mktime(
        datetime.strptime(
            datetime.fromtimestamp(time.time()).date().strftime("%d/%m/%Y"),
            "%d/%m/%Y")
        .timetuple())
    new_laws = Law.select(graph).where(f"_.timestamp = {int(today_timestamp)}")
    user = User.safeSelect(graph=graph ,token=user_id)
    inv = user.involvement_level
    res = []
    for law in new_laws:
        law_latest_vote = getLatestVoteForLaw(graph=graph, law=law)
        if law_latest_vote.num_of_electors_voted > inv:
            res.append(law.name)
    return res


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
    query = f"MATCH (e:{ElectedOfficial.__name__}) MATCH (v:{Vote.__name__}) MATCH (p:{Party.__name__}) " \
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
    tag_query = "" if tag is None else f"MATCH (t:{Tag.__name__}) WHERE (l)-[:{TAGGED_AS}]->(t) AND t.name='{tag}'"
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
    start_date = time.mktime(datetime.strptime(start_date, "%d/%m/%Y").timetuple())
    end_date = time.mktime(datetime.strptime(end_date, "%d/%m/%Y").timetuple())
    law_set = Law.select(graph)\
        .where("{}<= _.timestamp <={}".format(start_date, end_date))
    res = {}
    for law in law_set:
        res[law.name] = {"link" : law.link,
                         "description" : law.description}
                         #"tags" : law.tags_votes} #TODO: change to top 2 tags
    return res


def countPartyVotes(data):
    res = {}
    for selection in data:
        if res.get(selection["p.name"]) is None:
            res[selection["p.name"]]= {"count" : 1,
                                       "elected_officials" : [selection["e"].properties]}
        else:
            res[selection["p.name"]]["count"] += 1
            res[selection["p.name"]]["elected_officials"].append(selection["e"].properties)
    return res

def calculateStats(voted_for, voted_against, missing, abstained):
    res = {}

    for party, votes in voted_for.items():
        res[party] = {VOTED_FOR : votes}


    for party, votes in voted_against.items():
        if res.get(party) is None:
            res[party] = {VOTED_AGAINST : votes}
        else:
            res[party][VOTED_AGAINST] = votes

    for party, votes in missing.items():
        if res.get(party) is None:
            res[party] = {ELECTED_MISSING : votes}
        else:
            res[party][ELECTED_MISSING] = votes

    for party, votes in abstained.items():
        if res.get(party) is None:
            res[party] = {ELECTED_ABSTAINED : votes}
        else:
            res[party][ELECTED_ABSTAINED] = votes

    return res

def createStatsResponse(user_party, user_vote, votes):
    res = {}
    for party_name, party_vote in votes.items():
        total_votes = sum(x["count"] for x in party_vote.values())
        voted_like_user = party_vote.get(user_vote)["count"] if party_vote.get(user_vote) is not None else 0
        res[party_name] = {"match": (voted_like_user / total_votes),
                           "is_users_party": True if user_party == party_name else False,
                           "elected_voted": {"for" : party_vote[VOTED_FOR] if party_vote.get(VOTED_FOR) is not None else {},
                                             "against": party_vote[VOTED_AGAINST] if party_vote.get(VOTED_AGAINST) is not None else {},
                                             "abstained": party_vote[ELECTED_ABSTAINED] if party_vote.get(ELECTED_ABSTAINED) is not None else {},
                                             "missing": party_vote[ELECTED_MISSING] if party_vote.get(ELECTED_ABSTAINED) is not None else {}}
                           }
    return res


def _getElectedOfficialLawStats(graph, law_name, user_vote, user_party):

    query = f"MATCH(l:{Law.__name__}) MATCH(v:{Vote.__name__}) MATCH(e:{ElectedOfficial.__name__}) MATCH(p:{Party.__name__}) WHERE (v)-[:{LAW}]->(l) "\
            +"AND (v)-[:{}]->(e) AND " \
            f"(e)-[:{MEMBER_OF_PARTY}]->(p) AND "\
            +"l.name = '{}' return e, p.name "\
            "ORDER BY v.timestamp DESCENDING"

    voted_for = graph.run(query.format(ELECTED_VOTED_FOR,law_name)).data()
    voted_against = graph.run(query.format(ELECTED_VOTED_AGAINST, law_name)).data()
    missing = graph.run(query.format(ELECTED_MISSING, law_name)).data()
    abstained = graph.run(query.format(ELECTED_ABSTAINED, law_name)).data()

    voted_for = countPartyVotes(voted_for)
    voted_against = countPartyVotes(voted_against)
    missing = countPartyVotes(missing)
    abstained = countPartyVotes(abstained)

    votes = calculateStats(voted_for, voted_against, missing, abstained)

    res = createStatsResponse(user_party, user_vote, votes)

    return res


def getElectedOfficialLawStats(graph, law_name, user_vote, user_id):
    user = User.safeSelect(graph = graph, token=user_id)
    user_party = list(user.associate_party)[0].name
    return _getElectedOfficialLawStats(graph=graph, law_name=law_name, user_vote=user_vote, user_party=user_party)



