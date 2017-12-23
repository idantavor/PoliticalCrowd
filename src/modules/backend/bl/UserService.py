from src.modules.dal.graphObjects.graphObjects import *


def isUserExist(graph, user_token):
    return graph.evaluate("MATCH (n:User) WHERE n.token = \"{x}\" RETURN n LIMIT 1", x=user_token) is not None


def getUserAge(userNode):
    curr_year = datetime.datetime.now().year
    return curr_year - userNode.birth_year







