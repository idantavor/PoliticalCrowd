from src.modules.dal.graphObjects.graphObjects import *


def getUserAge(userNode):
    curr_year = datetime.datetime.now().year
    return curr_year - int(userNode.birth_year)