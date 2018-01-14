import datetime
import json
import time
from os import system

from flask import jsonify
from py2neo import Graph

from src.modules.backend.common.APIConstants import VOTED_FOR
from src.modules.dal.GraphConnection import bolt_connect
from src.modules.dal.graphObjects.graphObjects import User, Residency, JobCategory, ELECTED_VOTED_FOR, Tag
from src.modules.dal.graphObjects.graphObjects import Party
from src.modules.dal.graphObjects.graphObjects import ElectedOfficial
from src.modules.dal.graphObjects.graphObjects import Law
from src.modules.backend.bl import LawService, UserService



graph = bolt_connect()

# for line in open("C:\\Users\\oferh_000\\PycharmProjects\\PoliticalCrowd\\resources\\Tags.txt", mode="r", encoding="UTF-8"):
#     Tag.createTag(graph, line.strip())
for law in Law.select(graph):
    user_id = '10'
    law_name = law.name
    user_personal_details = UserService.getPersonalPreferences(graph=graph, user_id=user_id)
    distribution = dict()

    if LawService.validUserVotesForDist(graph, law_name):
        distribution = UserService.getUsersDistForLaw(graph, law_name)

    distribution.update({"user_info": user_personal_details})


