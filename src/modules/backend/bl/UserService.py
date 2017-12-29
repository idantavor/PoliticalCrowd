from datetime import datetime

from src.modules.dal.graphObjects.graphObjects import *


def isUserExist(graph, user_token):
    return graph.evaluate("MATCH (n:User) WHERE n.token = \"{x}\" RETURN n LIMIT 1", x=user_token) is not None


def getUserAge(userNode):
    curr_year = datetime.datetime.now().year
    return curr_year - userNode.birth_year


def getUserPartiesVotesMatchByTag(graph, user_id, tag ,num_of_laws_backwards):
    query = f"MATCH(u:{User.__name__})-[user_vote]->(l:{Law.__name__})-[:{LAW}]->(v:{Vote.__name__})-[elected_vote]->(e:{ElectedOfficial.__name__})-[:{MEMBER_OF_PARTY}]->(p:{Party.__name__}) " \
            f"{'' if tag is None else ' MATCH(t:{}'.format(Tag.__name__)})"\
            f"WHERE u.token={user_id} " \
            f"{'' if tag is None else 'AND (l)-[:{}]->(t)'.format(TAGGED_AS)}" \
            f"RETURN user_vote, l, elected_vote, v.date,e,p.name " \
            f"ORDER BY l.timestamp DESCENDING " \
            f"LIMIT {num_of_laws_backwards}"

    graph.run(query)










