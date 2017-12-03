import datetime
import time
from py2neo import Graph, NodeSelector


from modules.dal.graphObjects.graphObjects import User
from modules.dal.graphObjects.graphObjects import Party
from modules.dal.graphObjects.graphObjects import ElectedOfficial
from modules.dal.graphObjects.graphObjects import Law
from modules.dal.relations.Relations import VOTED_FOR, VOTED_AGAINST, ELECTED_VOTED_FOR_FIRST, ELECTED_VOTED_FOR_SECOND, \
    ELECTED_VOTED_FOR_THIRD, ELECTED_VOTED_AGAINST_FIRST, ELECTED_VOTED_AGAINST_SECOND, ELECTED_VOTED_AGAINST_THIRD, \
    ELECTED_ABSTAINED_FIRST, ELECTED_ABSTAINED_SECOND, ELECTED_ABSTAINED_THIRD, ELECTED_MISSING_FIRST, \
    ELECTED_MISSING_SECOND, ELECTED_MISSING_THIRD, ASSOCIATE_PARTY


def http_connect():
    return Graph("http://127.0.0.1:7474/db/data/", password="12345")

def bolt_connect():
    return Graph("bolt://127.0.0.1:7687/db/data/", password="12345")


def initDb():
    graph = bolt_connect()
    graph.begin(autocommit=True)
    graph.delete_all()

    #creation of graph objects
    ofer = User.createUser(token="1", job="הייטק", birthYear=1989, involvmentLevel="low", residancy="תל אביב")
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
relatedToQueries()





