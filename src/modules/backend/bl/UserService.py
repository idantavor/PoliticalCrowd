from datetime import datetime

import logging

from src.modules.dal.graphObjects.graphObjects import *
import datetime

logger = logging.getLogger(__name__)

def isUserExist(graph, user_token):
    return graph.evaluate(f"MATCH (n:User) WHERE n.token = '{user_token}' RETURN n LIMIT 1") is not None


def getUserAge(userNode):
    curr_year = datetime.datetime.now().year
    return curr_year - userNode.birth_year

# TODO cont.
def getUsersDistForLaw(law):
    voted_for =  law.users_voted_for
    voted_againts = law.users_voted_againts
    num_of_voters = len(voted_for) + len(voted_againts)




def getUserPartiesVotesMatchByTag(graph, user_id, tag ,num_of_laws_backwards):
    query = f"MATCH(u:{User.__name__})-[user_vote]->(l:{Law.__name__})-[:{LAW}]->(v:{Vote.__name__})-[elected_vote]->(e:{ElectedOfficial.__name__})-[:{MEMBER_OF_PARTY}]->(p:{Party.__name__}) " \
            f"{'' if tag is None else ' MATCH(t:{}'.format(Tag.__name__)})"\
            f"WHERE u.token={user_id} " \
            f"{'' if tag is None else 'AND (l)-[:{}]->(t)'.format(TAGGED_AS)}" \
            f"RETURN user_vote, l, elected_vote, v.date,e,p.name " \
            f"ORDER BY l.timestamp DESCENDING " \
            f"LIMIT {num_of_laws_backwards}"

    graph.run(query)










