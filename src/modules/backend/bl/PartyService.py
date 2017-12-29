from src.modules.backend.bl import LawService
from src.modules.backend.common import CommonUtils
from src.modules.dal.graphObjects.graphObjects import *
from src.modules.backend.app.WebAPI import app
import itertools

logger = app.logger

NUM_OF_PROPOSALS = "num_of_proposals"
ELECTED_PROPOSALS = "elected_proposals"
PARTY_EFFICIENCY = "Party Efficiency"
MEMBER_EFFICIENCY = "Memeber Efficiency"
PARTY_MISSING = "Party Missing"
MEMBER_MISSING = "Member Missing"


def _getPartyEfficiancy(graph, party, laws):
    num_of_members = len(party.party_members)
    wanted_num_of_votes = len(laws) * num_of_members
    real_num_of_votes = 0
    member_efficiency = {}

    logger.debug(f"Find efficiency for party: {party.name}")

    for law in laws:
        electors_voted_for_law = LawService.getAllElectedInPartyVotedInLaw(graph=graph, law=law, party=party)
        real_num_of_votes += len(electors_voted_for_law)
        for elect in electors_voted_for_law:
            if elect.name in member_efficiency:
                member_efficiency[elect.name] = member_efficiency[elect.name] + 1
            else:
                member_efficiency[elect.name] = 1

    party_efficiency = {PARTY_EFFICIENCY: real_num_of_votes / float(wanted_num_of_votes), MEMBER_EFFICIENCY: member_efficiency}

    logger.debug(f"for party:{party.name}, {str(party_efficiency)}")

    return party_efficiency


def getAllPartiesEfficiencyByTag(graph, tag, num_of_laws_backward):
    logger.debug(f"params: tag={tag}, num_of_laws={num_of_laws_backward}")

    parties_efficiancy = dict()
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)

    for party in Party.select(graph=graph):
        parties_efficiancy[party.name] = _getPartyEfficiancy(graph=graph, party=party, laws=laws)

    logger.debug(f"Parties Efficiancy: {str(parties_efficiancy)}")

    return parties_efficiancy


def getAllLawProposalPerParty(graph, tag, num_of_laws_backward):
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)
    proposed_by = [CommonUtils.getSingleItemInSet(law.proposed_by) for law in laws] # list of ElectedOfficial

    logger.debug(f"Proposals for laws are:{str(proposed_by)}. check for sanity:{CommonUtils.getSingleItemInSet(proposed_by[0].member_of_party).name}")

    total_num_of_laws = len(laws)
    all_proposals = dict()

    for party, elected_officals in itertools.groupby(proposed_by, key=lambda elected: CommonUtils.getSingleItemInSet(elected.member_of_party).name):
        elected_list = list(elected_officals)
        num_of_proposals = len(elected_list)
        elected_proposals = {name : len(list(group)) for name, group in itertools.groupby(elected_list, key=lambda elected: elected.name)}
        all_proposals[party.name] = {NUM_OF_PROPOSALS:(num_of_proposals/float(total_num_of_laws)), ELECTED_PROPOSALS: elected_proposals}

    return all_proposals


def _getPartyMissingFromLaws(graph, party, laws):
    member_missing = {}
    total = len(party.party_members) * len(laws)
    total_missing = 0
    for law in laws:
        electors_missing = LawService.getAllElectedInPartyMissingFromLaw(graph=graph, party=party, law=law)
        total_missing += len(electors_missing)
        for elector in electors_missing:
            if elector.name in member_missing:
                member_missing[elector.name] = member_missing[elector.name] + 1
            else:
                member_missing[elector.name] = 1

    party_missing = {PARTY_MISSING: total_missing/float(total), MEMBER_MISSING: member_missing}

    return party_missing


def absentFromVotesByParty(graph, tag, num_of_laws_backward):
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)
    parties_missing = dict()

    for party in Party.select(graph=graph):
        parties_missing[party.name] = _getPartyMissingFromLaws(graph=graph, party=party, laws=laws)

    logger.debug(f"Parties absent: {str(parties_missing)}")

    return parties_missing









