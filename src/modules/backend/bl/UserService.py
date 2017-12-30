from datetime import datetime

import logging

from src.modules.backend.common.APIConstants import AgeRange, JOB_FOR, JOB_AGAINST, RESIDENT_FOR, RESIDENT_AGAINST, \
    AGE_FOR, AGE_AGAINST, SAME, DIFF, MEMBER_ABSENT
from src.modules.dal.graphObjects.graphObjects import *
import datetime
from itertools import groupby

logger = logging.getLogger(__name__)

def isUserExist(graph, user_token):
    return graph.evaluate(f"MATCH (n:User) WHERE n.token = '{user_token}' RETURN n LIMIT 1") is not None


def getUserAge(user_node):
    curr_year = datetime.datetime.now().year
    return curr_year - user_node.birth_year


def getUserAgeRange(user_node):
    user_age = getUserAge(user_node)
    if user_age < AgeRange.Second:
        begin = str(AgeRange.First)
        end = str(AgeRange.Second)
    elif user_age < AgeRange.Third:
        begin = str(AgeRange.Second)
        end = str(AgeRange.Third)
    elif user_age < AgeRange.Fourth:
        begin = str(AgeRange.Third)
        end = str(AgeRange.Fourth)
    elif user_age < AgeRange.Fifth:
        begin = str(AgeRange.Fourth)
        end = str(AgeRange.Fifth)
    else:
        begin = str(AgeRange.Fifth)
        end = ""

    return f"{begin}-{end}"


def getUsersDistForLaw(graph, law_name):
    law = Law.safeSelect(graph=graph, name=law_name)
    voted_for =  list(law.users_voted_for)
    voted_againts = list(law.users_voted_againts)
    num_of_voters = len(voted_for) + len(voted_againts)

    job_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                      groupby(sorted(voted_for, key=lambda user: user.work_at.name), key=lambda user: user.work_at.name)}
    job_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                          groupby(sorted(voted_againts, key=lambda user: user.work_at.name), key=lambda user: user.work_at.name)}

    resident_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                           groupby(sorted(voted_for, key=lambda user: user.residing.name), key=lambda user: user.residing.name)}
    resident_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                               groupby(sorted(voted_againts, key=lambda user: user.residing.name), key=lambda user: user.residing.name)}

    age_range_for_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                            groupby(sorted(voted_for, key=lambda user: getUserAgeRange(user)), key=lambda user: getUserAgeRange(user))}
    age_range_againts_groups = {key: (len(list(group))/float(num_of_voters)) for key, group in
                                groupby(sorted(voted_againts, key=lambda user: getUserAgeRange(user)), key=lambda user: getUserAgeRange(user))}

    distribution = {JOB_FOR: job_for_groups, JOB_AGAINST: job_againts_groups,
                    RESIDENT_FOR: resident_for_groups, RESIDENT_AGAINST: resident_againts_groups,
                    AGE_FOR: age_range_for_groups, AGE_AGAINST: age_range_againts_groups}

    return jsonify(distribution)


def getUserMatchForOfficial(graph, user_id, member_name, tag=None):

    tag_match = "" if tag is None else f"AND t.name={tag.name} AND (l)-[:{TAGGED_AS}]->(t)"

    query_total_laws = f"MATCH (u:{User.__name__}), (l:{Law.__name__}), (t:{Tag.__name__}) " \
                       f"WHERE u.token={user_id} {tag_match} " \
                       f"AND ((u)-[:{VOTED_FOR}]->(l) OR (u)-[:{VOTED_AGAINST}]->(l)) " \
                       f"RETURN COUNT(DISTINCT (l))"

    num_of_total = graph.run(query_total_laws).data()

    query_same = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__}, (t:{Tag.__name__}) " \
                 f"WHERE u.token={user_id} AND e.name='{member_name}' {tag_match}" \
                 f"AND (v)-[:{LAW}]->(l) AND " \
                 f"(((u)-[:{VOTED_FOR}]->(l) AND (v)-[:{ELECTED_VOTED_FOR}]->(e)) OR " \
                 f"((u)-[:{VOTED_AGAINST}]->(l) AND (v)-[:{ELECTED_VOTED_AGAINST}]->(e))) " \
                 f"RETURN COUNT(DISTINCT (l))"

    num_of_same = graph.run(query_same).data()

    query_different = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__} " \
                      f"WHERE u.token={user_id} AND e.name='{member_name}' {tag_match}" \
                      f"AND (v)-[:{LAW}]->(l) AND " \
                      f"(((u)-[:{VOTED_FOR}]->(l) AND (v)-[:{ELECTED_VOTED_AGAINST}]->(e)) OR " \
                      f"((u)-[:{VOTED_AGAINST}]->(l) AND (v)-[:{ELECTED_VOTED_FOR}]->(e))) " \
                      f"RETURN COUNT(DISTINCT (l))"

    num_of_different = graph.run(query_different).data()

    query_member_absent = f"MATCH (u:{User.__name__}), (e:{ElectedOfficial.__name__}), (l:{Law.__name__}), (v:{Vote.__name__}, (t:{Tag.__name__}) " \
                          f"WHERE u.token={user_id} AND e.name='{member_name}' {tag_match}" \
                          f"AND (v)-[:{LAW}]->(l) AND " \
                          f"(((u)-[:{VOTED_FOR}]->(l) AND (v)-[:{ELECTED_MISSING}]->(e)) OR " \
                          f"((u)-[:{VOTED_AGAINST}]->(l) AND (v)-[:{ELECTED_MISSING}]->(e))) " \
                          f"RETURN COUNT(DISTINCT (l))"

    num_of_member_absent = graph.run(query_member_absent).data()

    match_dict = {SAME: num_of_same/num_of_total, DIFF: num_of_different/num_of_total, MEMBER_ABSENT: num_of_member_absent/num_of_total}

    return match_dict


def getUserPartiesVotesMatchByTag(graph, user_id, tag ,num_of_laws_backwards):
    query = f"MATCH(u:{User.__name__})-[user_vote]->(l:{Law.__name__})-[:{LAW}]->(v:{Vote.__name__})-[elected_vote]->(e:{ElectedOfficial.__name__})-[:{MEMBER_OF_PARTY}]->(p:{Party.__name__}) " \
            f"{'' if tag is None else ' MATCH(t:{}'.format(Tag.__name__)})"\
            f"WHERE u.token={user_id} " \
            f"{'' if tag is None else 'AND (l)-[:{}]->(t)'.format(TAGGED_AS)}" \
            f"RETURN user_vote, l, elected_vote, v.date,e,p.name " \
            f"ORDER BY l.timestamp DESCENDING " \
            f"LIMIT {num_of_laws_backwards}"

    graph.run(query)









