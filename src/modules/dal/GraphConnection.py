from py2neo import Graph


def bolt_connect():
    return Graph("bolt://104.196.62.104:7687/db/data/",password="bibikiller")

def http_connect():
    return Graph("http://104.196.62.104:7474/db/data/",password="bibikiller")