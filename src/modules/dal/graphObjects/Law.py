from py2neo.ogm import *

from src.modules.dal.graphObjects.ElectedOfficial import ElectedOfficials
from src.modules.dal.relations.Relations import VOTED_FOR, VOTED_AGAINST


class Law(GraphObject):
    __primarykey__ = "name"

    name = Property()
    date = Property(key="date")
    status = Property(key="status")
    description = Property()
    link = Property()

    user_voted_for = RelatedFrom("User", VOTED_FOR)
    user_voted_against   = RelatedFrom("User", VOTED_AGAINST)

    elected_voted_for_first = RelatedTo(ElectedOfficials)
    elected_voted_for_second = RelatedTo(ElectedOfficials)
    elected_voted_for_third = RelatedTo(ElectedOfficials)

    elected_voted_against_first = RelatedTo(ElectedOfficials)
    elected_voted_against_second = RelatedTo(ElectedOfficials)
    elected_voted_against_third = RelatedTo(ElectedOfficials)

    elected_abstained_first = RelatedTo(ElectedOfficials)
    elected_abstained_second = RelatedTo(ElectedOfficials)
    elected_abstained_third = RelatedTo(ElectedOfficials)

    elected_missing_first = RelatedTo(ElectedOfficials)
    elected_missing_second = RelatedTo(ElectedOfficials)
    elected_missing_third = RelatedTo(ElectedOfficials)

    proposed_by = RelatedTo(ElectedOfficials)


