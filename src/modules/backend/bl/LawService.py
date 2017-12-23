from flask import json

from src.modules.backend.app.WebAPI import app
from src.modules.backend.bl.UserService import isUserExist
from src.modules.backend.common.APIConstants import VOTED_FOR, VOTED_AGAINST, VOTED_ABSTAINED, VOTED_MISSING
from src.modules.dal.graphObjects.graphObjects import User, Law
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


def getAllElectedVotedForLaw(law):
    curr_vote = getLatestVote(law)
    total_votes = list(curr_vote.elected_voted_for | curr_vote.elected_voted_against | curr_vote.elected_abstained)
    return total_votes


def getNumOfLawsByTag(graph, tag, num_of_laws):
    laws = list(Law.select(graph=graph))
    filtered_laws = laws if tag is None else list(filter(lambda law: tag in itertools.islice(sorted(law.tags_votes, key=itemgetter(1), reverse=True), 2), laws))
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


def getLatestVote(law):
    return sorted(list(law.elected_officials_votes), key=lambda v : v.date, reverse=True)[0]

def insertVotesByType(ret, vote_type, key_name):
    for elected in list(vote_type):
        party = list(elected.member_of_party)[0]
        if ret[party.name] is None:
            ret[party.name] = {key_name : 1}
        elif ret[party.name][key_name] is None:
            ret[party.name][key_name] = 1
        else:
            ret[party.name][key_name] = ret[party.name][key_name] + 1

def getLawStats(graph, law_name, user_vote, user_id):
    law = Law.safeSelect(graph= graph, name= law_name)
    votes = {}
    vote = getLatestVote(law)
    insertVotesByType(ret=votes, vote_type=vote.elected_voted_for, key_name=VOTED_FOR)
    insertVotesByType(ret=votes, vote_type=vote.elected_voted_against, key_name=VOTED_AGAINST)
    insertVotesByType(ret=votes, vote_type=vote.elected_missing, key_name=VOTED_ABSTAINED)
    insertVotesByType(ret=votes, vote_type=vote.elected_abstained, key_name=VOTED_MISSING)

    user = User.safeSelect(graph = graph, token=user_id)
    user_party = list(user.associate_party)[0].name

    res = {}
    for party in votes:
        total_votes = sum(x for x in party.values())
        voted_like_user = party[user_vote]
        res[party.name] = {"match": (voted_like_user / total_votes),
                           "is_users_party" : True if user_party == party.name else False}

    return res

