import datetime
import json
import time
from os import system

from flask import jsonify
from py2neo import Graph

from src.modules.backend.common.APIConstants import VOTED_FOR, InvolvementLevel
from src.modules.dal.GraphConnection import bolt_connect
from src.modules.dal.graphObjects.graphObjects import User, Residency, JobCategory, ELECTED_VOTED_FOR, Tag
from src.modules.dal.graphObjects.graphObjects import Party
from src.modules.dal.graphObjects.graphObjects import ElectedOfficial
from src.modules.dal.graphObjects.graphObjects import Law
from src.modules.backend.bl import LawService, UserService



graph = bolt_connect()

# for line in open("C:\\Users\\oferh_000\\PycharmProjects\\PoliticalCrowd\\resources\\Tags.txt", mode="r", encoding="UTF-8"):
#     Tag.createTag(graph, line.strip())
# for law in Law.select(graph):
#     user_id = '10'
#     law_name = law.name
#     user_personal_details = UserService.getPersonalPreferences(graph=graph, user_id=user_id)
#     distribution = dict()
#
#     if LawService.validUserVotesForDist(graph, law_name):
#         distribution = UserService.getUsersDistForLaw(graph, law_name)
#
#     distribution.update({"user_info": user_personal_details})

import random

tags = ['טכנולוגיה', 'תרבות', 'כלכלה', 'ביטחון', 'פלילי', 'חיי אדם',
        'רפואה', 'סוציאליסטי', 'קפיטליסטי', 'ימני', 'שמאלני', 'דת',
        'בני מיעוטים', 'איכות הסביבה', 'תשתיות', 'משאבי טבע', 'חינוך', 'מיסים']

num_of_users = 20
jobs = list(JobCategory.select(graph))
cities = list(Residency.select(graph))
parties = list(Party.select(graph))
laws=list(Law.select(graph))

job_lst =[]
city_lst =[]
party_lst = []
year_lst=[1980, 1960, 1990, 1930]
for i in range(0, 5):
    job_lst.append(jobs[i].name)
    city_lst.append(cities[i].name)
    party_lst.append(parties[i].name)


user_lst = []
for i in range(11,num_of_users):
    user_lst.append(User.createUser(graph, str(i), job_lst[i%5], year_lst[i%4], city_lst[i%5], InvolvementLevel.MEDIUM))


for user in user_lst:
    for law in laws:
        vote = random.choice([True, False])
        user.voteLaw(graph, law.name, vote)
        user.tagLaw(graph, law.name, random.choice(tags))


