from src.modules.backend.bl import LawService
from src.modules.backend.common.APIConstants import ELECTED_OFFICIAL
from src.modules.dal.graphObjects.graphObjects import *
from operator import itemgetter
from src.modules.backend.app.WebAPI import app
import itertools

logger = app.logger


def _getPartyEfficiancy(graph, party, laws):
    num_of_members = len(party.party_members)
    wanted_num_of_votes = len(laws) * num_of_members
    real_num_of_votes = 0

    logger.debug(f"Find efficiency for party: {party.name}")

    for law in laws:
        total_votes = LawService.getAllElectedVotedForLaw(law)
        real_num_of_votes += len(list(filter(lambda elected_official: elected_official in party.party_members, total_votes)))

    logger.debug(f"for party:{party.name}, wanted is:{wanted_num_of_votes}, real is:{real_num_of_votes} -> Efficiency is:{real_num_of_votes / wanted_num_of_votes}")

    return real_num_of_votes / wanted_num_of_votes


def _getMemberEfficiency(graph, member, laws):
    wanted_num_of_votes = len(laws)

    logger.debug(f"Find efficiency for: {member.name}")

    real_num_of_votes = len(list(filter(lambda law: member in LawService.getAllElectedVotedForLaw(law), laws)))

    logger.debug(f"for member:{member.name}, wanted is: {wanted_num_of_votes}, real is: {real_num_of_votes} -> Efficiency is:{real_num_of_votes / wanted_num_of_votes}")

    return real_num_of_votes / wanted_num_of_votes


def getAllPartiesEfficiencyByTag(graph, tag, num_of_laws_backward):
    logger.debug(f"params: tag={tag}, num_of_laws={num_of_laws_backward}")

    parties_efficiancy = dict()
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)
    logger.debug(f"laws: {str(laws)}")

    for party in Party.select(graph=graph):
        party_efficiancy = _getPartyEfficiancy(graph=graph, party=party, laws=laws)
        members_efficiancy = dict()
        for party_member in party.party_members:
            members_efficiancy[party_member.name] = _getMemberEfficiency(graph=graph, member=party_member, laws=laws)
        parties_efficiancy[party.name] = {"Party Efficiancy": party_efficiancy, "Members Efficiancy": members_efficiancy}

    logger.debug(f"Parties Efficiancy: {str(parties_efficiancy)}")

    return parties_efficiancy


def lawProposalPerParty(graph, tag, num_of_laws_backward):
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)
    total_num_of_laws = len(laws)

    for party in Party.select(graph=graph):
        pass



