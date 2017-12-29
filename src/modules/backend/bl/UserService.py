from src.modules.dal.graphObjects.graphObjects import *
import datetime

def isUserExist(graph, user_token):
    return graph.evaluate("MATCH (n:User) WHERE n.token = \"{x}\" RETURN n LIMIT 1", x=user_token) is not None


def getUserAge(userNode):
    curr_year = datetime.datetime.now().year
    return curr_year - userNode.birth_year

# TODO cont.
def getUsersDistForLaw(law):
    voted_for =  law.users_voted_for
    voted_againts = law.users_voted_againts
    num_of_voters = len(voted_for) + len(voted_againts)









