from py2neo.ogm import *

from src.modules.dal.graphObjects.Party import Party
from src.modules.dal.relations.Relations import ELECTED_VOTED_FOR_FIRST, ELECTED_VOTED_FOR_THIRD, \
    ELECTED_VOTED_FOR_SECOND, ELECTED_VOTED_AGAINST_FIRST, ELECTED_VOTED_AGAINST_SECOND, ELECTED_VOTED_AGAINST_THIRD, \
    ELECTED_ABSTAINED_THIRD, ELECTED_ABSTAINED_SECOND, ELECTED_ABSTAINED_FIRST, ELECTED_MISSING_THIRD, \
    ELECTED_MISSING_SECOND, ELECTED_MISSING_FIRST


class ElectedOfficials(GraphObject):
    __primarykey__ = "name"

    name = Property()
    active = Property(key="active")
    title = Property()

    associate_party = RelatedTo(Party)

    voted_for_first = RelatedFrom("Law", ELECTED_VOTED_FOR_FIRST)
    voted_for_second = RelatedFrom("Law", ELECTED_VOTED_FOR_SECOND)
    voted_for_third = RelatedFrom("Law", ELECTED_VOTED_FOR_THIRD)

    voted_against_first = RelatedFrom("Law", ELECTED_VOTED_AGAINST_FIRST)
    voted_against_second = RelatedFrom("Law", ELECTED_VOTED_AGAINST_SECOND)
    voted_against_third = RelatedFrom("Law", ELECTED_VOTED_AGAINST_THIRD)

    abstained_first = RelatedFrom("Law", ELECTED_ABSTAINED_FIRST)
    abstained_second = RelatedFrom("Law", ELECTED_ABSTAINED_SECOND)
    abstained_third = RelatedFrom("Law", ELECTED_ABSTAINED_THIRD)

    missing_first = RelatedFrom("Law", ELECTED_MISSING_FIRST)
    missing_second = RelatedFrom("Law", ELECTED_MISSING_SECOND)
    missing_third = RelatedFrom("Law", ELECTED_MISSING_THIRD)

