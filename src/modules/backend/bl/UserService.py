from datetime import datetime, timedelta

import logging

from src.modules.backend.bl import LawService
from src.modules.backend.common.APIConstants import AgeRange, JOB_FOR, JOB_AGAINST, RESIDENT_FOR, RESIDENT_AGAINST, \
    AGE_FOR, AGE_AGAINST, SAME, DIFF, MEMBER_ABSENT, AGE, RESIDENCY, JOB, PARTY, BIRTH_YEAR, INVOLVEMENT_LEVEL
from src.modules.dal.graphObjects.graphObjects import *
from itertools import groupby

logger = logging.getLogger(__name__)

def isUserExist(graph, user_token):
    return graph.evaluate(f"MATCH (n:User) WHERE n.token = '{user_token}' RETURN n LIMIT 1") is not None


def getUserAge(user_node):
    curr_year = datetime.now().year
    return curr_year - int(user_node.birth_year)


def getUserParty(graph, user_id):
    user = User.safeSelect(graph=graph, token=user_id)
    return list(user.associate_party)[0].name


def getUserAgeRange(user_node):
    user_age = getUserAge(user_node)
    if user_age < AgeRange.Second.value:
        begin = str(AgeRange.First.value)
        end = str(AgeRange.Second.value)
    elif user_age < AgeRange.Third.value:
        begin = str(AgeRange.Second.value)
        end = str(AgeRange.Third.value)
    elif user_age < AgeRange.Fourth.value:
        begin = str(AgeRange.Third.value)
        end = str(AgeRange.Fourth.value)
    elif user_age < AgeRange.Fifth.value:
        begin = str(AgeRange.Fourth.value)
        end = str(AgeRange.Fifth.value)
    else:
        return str(AgeRange.Fifth.value)+"+"


    return f"{begin}-{end}"


def getPersonalPreferences(graph, user_id):
    user = User.safeSelect(graph=graph, token=user_id)
    details = dict()
    details[JOB] = list(user.work_at)[0].name
    details[RESIDENCY] = list(user.residing)[0].name
    details[AGE] = getUserAgeRange(user)
    return details

def getPersonalInfo(graph, user_id):
    user = User.safeSelect(graph=graph, token=user_id)
    details = dict()
    details[JOB] = list(user.work_at)[0].name
    details[RESIDENCY] = list(user.residing)[0].name
    details[BIRTH_YEAR] = user.birth_year
    details[PARTY] = list(user.associate_party)[0].name
    details[INVOLVEMENT_LEVEL] = InvolvementLevel(user.involvement_level).name
    return details

def getUsersDistForLaw(graph, law_name):
    law = Law.safeSelect(graph=graph, name=law_name)
    voted_for =  list(law.users_voted_for)
    voted_againts = list(law.users_voted_againts)
    num_of_voters = len(voted_for) + len(voted_againts)

    job_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                      groupby(sorted(voted_for, key=lambda user: list(user.work_at)[0].name), key=lambda user: list(user.work_at)[0].name)}
    job_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                          groupby(sorted(voted_againts, key=lambda user: list(user.work_at)[0].name), key=lambda user: list(user.work_at)[0].name)}

    resident_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                           groupby(sorted(voted_for, key=lambda user: list(user.residing)[0].name), key=lambda user: list(user.residing)[0].name)}
    resident_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                               groupby(sorted(voted_againts, key=lambda user: list(user.residing)[0].name), key=lambda user: list(user.residing)[0].name)}

    age_range_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                            groupby(sorted(voted_for, key=lambda user: getUserAgeRange(user)), key=lambda user: getUserAgeRange(user))}
    age_range_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                                groupby(sorted(voted_againts, key=lambda user: getUserAgeRange(user)), key=lambda user: getUserAgeRange(user))}

    distribution = {JOB_FOR: job_for_groups, JOB_AGAINST: job_againts_groups,
                    RESIDENT_FOR: resident_for_groups, RESIDENT_AGAINST: resident_againts_groups,
                    AGE_FOR: age_range_for_groups, AGE_AGAINST: age_range_againts_groups}

    return distribution


def getUserMatchForOfficial(graph, user_id, member_name, tag=None):
    today_timestamp = time.mktime(
        datetime.strptime(
            datetime.fromtimestamp(time.time()).date().strftime("%d/%m/%Y"),
            "%d/%m/%Y")
            .timetuple())
    old_timestamp = time.mktime(
        datetime.strptime(
            (datetime.fromtimestamp(time.time()) - timedelta(days=30)).date().strftime("%d/%m/%Y"),
            "%d/%m/%Y")
            .timetuple())


    if tag == "כללי":
        tag = None
    tag_match = "" if tag is None else f"AND t.name='{tag}' AND (l:{Law.__name__})-[:{TAGGED_AS}]->(t:{Tag.__name__})"

    query_total_laws = f"MATCH (u:{User.__name__}), (l:{Law.__name__}), (t:{Tag.__name__}), (v:{Vote.__name__}) " \
                       f"WHERE u.token='{user_id}' {tag_match} " \
                       f"AND ((u)-[:{VOTED_FOR}]->(l) OR (u)-[:{VOTED_AGAINST}]->(l)) " \
                       f"AND (v)-[:{LAW}]->(l) " \
                       f"AND {old_timestamp}<= l.timestamp <= {today_timestamp} " \
                       f"RETURN COUNT(DISTINCT (v))"

    num_of_total = float(list(graph.run(query_total_laws).data()[0].items())[0][1])

    query_same = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__}), (t:{Tag.__name__}) " \
                 f"WHERE u.token='{user_id}' AND e.name='{member_name}' {tag_match}" \
                 f"AND (v)-[:{LAW}]->(l) AND " \
                 f"(((u)-[:{VOTED_FOR}]->(l) AND (v)-[:{ELECTED_VOTED_FOR}]->(e)) OR " \
                 f"((u)-[:{VOTED_AGAINST}]->(l) AND (v)-[:{ELECTED_VOTED_AGAINST}]->(e))) " \
                 f"AND {old_timestamp}<= l.timestamp <= {today_timestamp} " \
                 f"RETURN COUNT(DISTINCT (v))"

    num_of_same = float(list(graph.run(query_same).data()[0].items())[0][1])

    query_different = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__}), (t:{Tag.__name__}) " \
                      f"WHERE u.token='{user_id}' AND e.name='{member_name}' {tag_match}" \
                      f"AND (v)-[:{LAW}]->(l) AND " \
                      f"(((u)-[:{VOTED_FOR}]->(l) AND (v)-[:{ELECTED_VOTED_AGAINST}]->(e)) OR " \
                      f"((u)-[:{VOTED_AGAINST}]->(l) AND (v)-[:{ELECTED_VOTED_FOR}]->(e))) " \
                      f"AND {old_timestamp}<= l.timestamp <= {today_timestamp} " \
                      f"RETURN COUNT(DISTINCT (v))"

    num_of_different = float(list(graph.run(query_different).data()[0].items())[0][1])

    query_member_absent = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__}), (t:{Tag.__name__}) " \
                          f"WHERE u.token='{user_id}' AND e.name='{member_name}' {tag_match}" \
                          f"AND (v)-[:{LAW}]->(l) AND " \
                          f"(((u)-[:{VOTED_FOR}]->(l) AND ((v)-[:{ELECTED_ABSTAINED}]->(e) OR (v)-[:{ELECTED_MISSING}]->(e))) OR " \
                          f"((u)-[:{VOTED_AGAINST}]->(l) AND ((v)-[:{ELECTED_ABSTAINED}]->(e) OR (v)-[:{ELECTED_MISSING}]->(e)))) " \
                          f"AND {old_timestamp}<= l.timestamp <= {today_timestamp} " \
                          f"RETURN COUNT(DISTINCT (v))"

    num_of_member_absent = float(list(graph.run(query_member_absent).data()[0].items())[0][1])

    if int(num_of_total) == 0:
        num_of_total = 1.0

    match_dict = {SAME: (num_of_same/num_of_total), DIFF: (num_of_different/num_of_total), MEMBER_ABSENT: (num_of_member_absent/num_of_total)}

    return match_dict



def getUserPartiesVotesMatchByTag(graph, user_id, tag ,num_of_laws_backwards = 15):
    if tag == "כללי":
        tag = None
    tag_query = f" AND t.name='{tag}'"
    query = f"MATCH(u:{User.__name__})-[user_vote]->(l:{Law.__name__}){'' if tag is None else '-[:{}]->(t:{})'.format(TAGGED_AS, Tag.__name__)} " \
            f"WHERE u.token='{user_id}'{'' if tag is None else tag_query} " \
            f"RETURN user_vote, l.name ORDER BY l.timestamp DESCENDING LIMIT {num_of_laws_backwards}"

    last_laws_voted = graph.run(query).data()
    if not last_laws_voted:
        return {}
    res = {}
    law_num = 0
    user = User.safeSelect(graph=graph, token=user_id)
    user_party = list(user.associate_party)[0].name
    for selection in last_laws_voted:
        if selection["user_vote"]._Relationship__type == TAGGED_AS:
            continue
        law_votes = LawService._getElectedOfficialLawStats(graph=graph, law_name=selection["l.name"], user_party=user_party,user_vote=selection["user_vote"]._Relationship__type)
        for party, info in law_votes.items():
            if res.get(party) is None:
                res[party] = {"match" : info["match"],
                              "is_users_party" : info["is_users_party"]}
            else:
                res[party]["match"] += info["match"]
        law_num += 1
    for party, match in res.items():
        res[party] = {"match" :(match["match"] / law_num),
                      "is_users_party" : match["is_users_party"]}

    return res


def getUserVoteForLaw(graph, user_id, law_name):
    user = User.safeSelect(graph=graph, token=user_id)
    law = Law.safeSelect(graph=graph, law_name=law_name)
    return VOTED_FOR if law in list(user.voted_for) else VOTED_AGAINST














