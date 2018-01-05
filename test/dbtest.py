import datetime
import json
import time
from os import system

from py2neo import Graph

from src.modules.dal.GraphConnection import bolt_connect
from src.modules.dal.graphObjects.graphObjects import User, Residency, JobCategory, ELECTED_VOTED_FOR, Tag
from src.modules.dal.graphObjects.graphObjects import Party
from src.modules.dal.graphObjects.graphObjects import ElectedOfficial
from src.modules.dal.graphObjects.graphObjects import Law

#def http_connect():
#    return Graph("http://127.0.0.1:7474/db/data/", password="12345")
    #return Graph("http://5.29.28.68:7474/db/data/", username="neo4j", password="bibikiller")

#def bolt_connect():
#    return Graph("bolt://127.0.0.1:7687/db/data/",password="12345")
    #return Graph("bolt://5.29.28.68:7687/db/data/", username="neo4j", password="bibikiller")


def initDb():
    graph = None #bolt_connect()
    graph.begin(autocommit=True)
    graph.delete_all()

    #creation of graph objects
    ofer = User.createUser(token="1", job="הייטק", birthYear=1989, involvementLevel="low", residancy="תל אביב")
    likud = Party.createParty(name="ליכוד", agenda="להיות חארות")
    orenHazan = ElectedOfficial.createElectedOfficial(name="אורן חזן", active=True, title="חבר כנסת")
    stupid_law = Law.createLaw(name="חוק דבילי", link="www.fuckme.com", status="FIRST_CALL", timestamp=datetime.datetime.now().__str__(), description="חוק דבילי")
    ofer.member_follows.add(orenHazan)
    ofer.voted_against.add(stupid_law)
    orenHazan.member_of_party.add(likud)
    stupid_law.elected_voted_for_first.add(orenHazan)
    stupid_law.elected_voted_for_second.add(orenHazan)
    stupid_law.elected_voted_for_third.add(orenHazan)
    ofer.associate_party.add(likud)
    graph.push(ofer)
    graph.push(orenHazan)
    graph.push(stupid_law)
    graph.push(likud)


def selectionObjectPrints():
    graph = None #bolt_connect()
    ofer = User.select(graph, primary_value="1").first()
    print(ofer)
    law = Law.select(graph, primary_value="חוק דבילי").first()
    print(law)
    oren = ElectedOfficial.select(graph, primary_value="אורן חזן").first()
    print(oren)
    party = Party.select(graph, primary_value="ליכוד").first()
    print(party)

def relatedFromQueries():
    graph = None #bolt_connect()
    party = Party.select(graph, primary_value="ליכוד").first()
    pp = party.party_members
    print("elected official members:")
    for k in pp:
        print(k)

    print("user follows:")
    ppp = party.user_follows
    for k in ppp:
        print(k)

    oren = ElectedOfficial.select(graph, primary_value="אורן חזן").first()

    print("oren hazans votes for:")
    ss = oren.voted_for_first
    for k in ss:
        print(k)

def relatedToQueries():
    graph = None #bolt_connect()
    ofer = User.select(graph, primary_value="1").first()
    print("parties ofer selected (can't enforce only 1 by neo4j)")
    for k in ofer.associate_party:
        print(k.name)
        print(k.agenda)

    k = list(ofer.voted_against)[0]
    print(k.name +" users token voted for:")
    for s  in k.user_voted_for:
        print(s.token)
    print("-------")
    print(k.name + " users voted against:")
    for s  in k.user_voted_against:
        print(s.token)



# enable all for first time test

#initDb()
#selectionObjectPrints()
#relatedFromQueries()
#relatedToQueries()


graph = bolt_connect()

# for line in open("C:\\Users\\oferh_000\\PycharmProjects\\PoliticalCrowd\\resources\\Tags.txt", mode="r", encoding="UTF-8"):
#     Tag.createTag(graph, line.strip())
for law in Law.select(graph):
    law.tags_votes=json.dumps(dict())
    graph.push(law)
#a = graph.run("MATCH(l:Law) MATCH(v:Vote) MATCH(e:ElectedOfficial) MATCH(p:Party) WHERE (v)-[:LAW]->(l) AND (v)-[:ELECTED_VOTED_FOR]->(e) AND (e)-[:MEMBER_OF_PARTY]->(p) AND l.name CONTAINS 'בריאות' return e, p.name")
#o  = ElectedOfficial.select(graph,primary_value="דוד אזולאי")\
#    .where("'{}' IN _.member_of_party".format('ש"ס'))
# query = "MATCH(l:Law) MATCH(v:Vote) MATCH(e:ElectedOfficial) MATCH(p:Party) WHERE (v)-[:LAW]->(l) AND (v)-[:{}]->(e) AND (e)-[:MEMBER_OF_PARTY]->(p) AND l.name CONTAINS '{}' return e, p.name"
# voted_for = graph.run(query.format(ELECTED_VOTED_FOR,"מחלת ה-SMA")).data()
# for x in voted_for:
#     s = ElectedOfficial.wrap(x["e"])
#
# a = Residency()
# a.name="תל אביב"
#
# graph.push(a)
#
# a = JobCategory()
# a.name="זגג"
#
# graph.push(a)




