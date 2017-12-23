import datetime

from py2neo import Graph

from src.modules.dal.graphObjects.graphObjects import *


def http_connect(ip="104.196.62.104", uname="neo4j", passwd="bibikiller"):
    return Graph("http://{}:7474/db/data/".format(ip), username=uname, password=passwd)

def bolt_connect(ip="104.196.62.104", uname="neo4j", passwd="bibikiller"):
    return Graph("bolt://{}:7687/db/data/".format(ip), username=uname, password=passwd)


def initDb():
    graph = bolt_connect()
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
    graph = bolt_connect()
    ofer = User.select(graph, primary_value="1").first()
    print(ofer)
    law = Law.select(graph, primary_value="חוק דבילי").first()
    print(law)
    oren = ElectedOfficial.select(graph, primary_value="אורן חזן").first()
    print(oren)
    party = Party.select(graph, primary_value="ליכוד").first()
    print(party)

def relatedFromQueries():
    graph = bolt_connect()
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
    graph = bolt_connect()
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





