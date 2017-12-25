from flask import json
from py2neo import Graph

from modules.backend.common.CommonUtils import runQueryOnGraph
from modules.dal.relations.Relations import ELECTED_VOTED_FOR, ELECTED_VOTED_AGAINST, ELECTED_MISSING, ELECTED_ABSTAINED
from src.modules.backend.app.WebAPI import app
from src.modules.backend.bl.UserService import isUserExist
from src.modules.backend.common.APIConstants import VOTED_FOR, VOTED_AGAINST, VOTED_ABSTAINED, VOTED_MISSING
from src.modules.dal.graphObjects.graphObjects import User, Law, ElectedOfficial
import itertools
from operator import itemgetter


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


# TODO Ram check if curr_vote.elected_voted_for return GraphObject or only the primary key
def getAllElectedVotedInLaw(graph, law):
    curr_vote = getLatestVote(law)
    # total_votes = graph.cypher.execute(f"MATCH ")
    # total_votes = ElectedOfficial.select(graph=graph).where(f"'{curr_vote.raw_title}' in _.voted_for")
    # total_votes = list(curr_vote.elected_voted_for | curr_vote.elected_voted_against | curr_vote.elected_abstained)
    return total_votes


def getAllElectedInPartyVotedInLaw(graph, law, party):
    curr_vote = getLatestVote(law)
    return list(graph.run(f"MATCH (e:{ElectedOfficial.__class__.name"))

def getNumOfLawsByTag(graph, tag, num_of_laws):
    filtered_laws = list(Law.select(graph=graph)) if tag is None else list(Law.select(graph=graph).where(f"'{tag}' in _.tagged_as")) ## TODO check if correct with db

    # law = list(Law.select(graph=graph))
    # filtered_laws = laws if tag is None else list(filter(lambda law: tag in itertools.islice(sorted(law.tags_votes, key=itemgetter(1), reverse=True), 2), laws))
    sorted_laws = filtered_laws.sort(key=lambda obj: obj.timestamp, reverse=True)
    top_laws = itertools.islice(sorted_laws, num_of_laws)
    return top_laws


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


def getLawStats(graph, law_name, user_vote, user_id):

    query = "MATCH(l:Law) MATCH(v:Vote) MATCH(e:ElectedOfficial) MATCH(p:Party) WHERE (v)-[:LAW]->(l) AND (v)-[:{}]->(e) AND (e)-[:MEMBER_OF_PARTY]->(p) AND l.name CONTAINS '{}' return e, p.name"
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

    res = {}
    for party_name, party_vote in votes.items():
        total_votes = sum(x["count"] for x in party_vote.values())
        voted_like_user = party_vote[user_vote]["count"]
        res[party_name] = {"match": (voted_like_user / total_votes),
                           "is_users_party" : True if user_party == party_name else False,
                           "elected_voted_for" : party_vote["elected_officials"]}

    return res

