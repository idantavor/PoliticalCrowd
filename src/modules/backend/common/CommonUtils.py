

def getSingleItemInSet(s):
    return iter(s).next()


class Node:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def runQueryOnGraph(graph, query):
    records = graph.run(query)
    return [Node(**(record['e'].properties)) for record in records.data()]