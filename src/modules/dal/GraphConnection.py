from py2neo import Graph


def bolt_connect():
    return Graph("bolt://127.0.0.1:7687/db/data/",password="bibikiller")
    #return Graph("bolt://127.0.0.1:7687/db/data/", password="bibikiller")

def http_connect():
    return Graph("http://127.0.0.1:7474/db/data/",password="bibikiller")