import os
import sys
sys.path.append('/home/i_tavor/PoliticalCrowd1')
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


#
# for t in tags:
#     Tag.createTag(graph, t)



# num_of_users = 50
# jobs = list(JobCategory.select(graph))
# cities = list(Residency.select(graph))
# parties = list(Party.select(graph))



# job_lst =[]
# city_lst =[]
# party_lst = []
# year_lst=[1980, 1960, 1990, 1930]
#
# for j in range(0,5):
#     party_lst.append(parties[j].name)
#
# i=0
# while len(job_lst) < 5:
#     if len(jobs[i].name) <= 6:
#         job_lst.append(jobs[i].name)
#     if len(cities[i].name) <= 6:
#         city_lst.append(cities[i].name)
#     i+=1

user_lst = list(User.select(graph))
# for i in range(0,num_of_users):
#     user_lst.append(User.createUser(graph, str(i), job_lst[i%5], year_lst[i%4], city_lst[i%5], InvolvementLevel.MEDIUM.value, party_lst[i%len(party_lst)]))


laws = []
s = graph.run("match(n:Law) return n order by n.timestamp descending limit 50")
for e in list(s):
    laws.append(Law.wrap(e[0]))

limit_laws = 50
law_count=0
for law in laws:
    law_count += 1
    if law_count == limit_laws:
        break
    for user in user_lst:
        vote = random.choice([True, False])
        user.voteLaw(graph, law.name, vote)
        user.tagLaw(graph, law.name, [random.choice(tags)])


