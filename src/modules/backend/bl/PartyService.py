from src.modules.backend.common.APIConstants import ELECTED_OFFICIAL
from src.modules.dal.graphObjects.graphObjects import *
from operator import itemgetter
from src.modules.backend.app.WebAPI import app
import itertools

logger = app.logger


def getPartyEfficiancy(graph, party, laws):
    num_of_members = len(party.party_members)
    wanted_num_of_votes = len(laws) * num_of_members
    real_num_of_votes = 0

    for law in laws:
        logger.debug(f"for law:{law.name}, the votes for are:{list(law.elected_officials_votes.elected_voted_for)}")
        real_num_of_votes += len(list(filter(lambda elected_official: elected_official.member_party.name == party.name,
                                             law.elected_officials_votes.elected_voted_for)))

        real_num_of_votes += len(list(filter(lambda elected_official: elected_official.member_party.name == party.name,
                                             law.elected_officials_votes.elected_voted_againts)))

        real_num_of_votes += len(list(filter(lambda elected_official: elected_official.member_party.name == party.name,
                                             law.elected_officials_votes.elected_abstained)))

    logger.debug(f"for party:{party.name}, Efficiancy is:{real_num_of_votes / wanted_num_of_votes}")

    return real_num_of_votes / wanted_num_of_votes

def getMemberEfficiancy(graph, member, laws):
    wanted_num_of_votes = len(laws)
    real_num_of_votes = 0

    logger.debug(f"member:{member.name}, voted_for:{member.voted_for}")

    real_num_of_votes += len(filter(lambda vote: vote.law in laws, member.voted_for))
    real_num_of_votes += len(filter(lambda vote: vote.law in laws, member.voted_against))
    real_num_of_votes += len(filter(lambda vote: vote.law in laws, member.voted_abstined))


    logger.debug(f"for member:{member.name}, Efficiancy is:{real_num_of_votes / wanted_num_of_votes}")

    return real_num_of_votes / wanted_num_of_votes


def getAllPartiesEfficiancyByTag(graph, tag, num_of_laws_backward):
    logger.debug(f"params: tag={tag}, num_of_laws={num_of_laws_backward}")

    parties_efficiancy = dict()
    laws = list(Law.select(graph=graph))
    filtered_laws = laws if tag is None else list(filter(lambda law: tag in sorted(law.tags_votes, key=itemgetter(1), reverse=True), laws))
    sorted_laws = filtered_laws.sort(key=lambda obj: obj.timestamp, reverse=True)
    top_laws = itertools.islice(sorted_laws, num_of_laws_backward)

    logger.debug(f"top laws: {str(top_laws)}")

    for party in Party.select(graph=graph):
        party_efficiancy = getPartyEfficiancy(graph=graph, party=party, laws=top_laws)
        members_efficiancy = dict()
        for party_member in party.party_members:
            members_efficiancy[party_member.name] = getMemberEfficiancy(graph=graph, member=party_member, laws=top_laws)
        parties_efficiancy[party.name] = {"Party Efficiancy": party_efficiancy, "Members Efficiancy": members_efficiancy}

    logger.debug(f"Parties Efficiancy: {str(parties_efficiancy)}")

    return parties_efficiancy

