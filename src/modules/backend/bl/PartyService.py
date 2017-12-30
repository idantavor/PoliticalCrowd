import logging
import pathlib

import os

from src.modules.backend.bl import LawService
from src.modules.dal.graphObjects.graphObjects import *
import itertools
from src.modules.dal.GraphConnection import bolt_connect
import json

logger = logging.getLogger(__name__)

NUM_OF_PROPOSALS = "num_of_proposals"
ELECTED_PROPOSALS = "elected_proposals"
PARTY_EFFICIENCY = "party_efficiency"
MEMBER_EFFICIENCY = "memeber_efficiency"
PARTY_MISSING = "party_missing"
MEMBER_MISSING = "member_missing"
LAW_PROPOSAL = "law_proposals"
ABSENT_STATS = "abesnt_stats"
ALL = "All"


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

    for name in member_efficiency.keys():
        member_efficiency[name] = member_efficiency[name]/float(real_num_of_votes)

    party_efficiency = {PARTY_EFFICIENCY: real_num_of_votes / float(wanted_num_of_votes), MEMBER_EFFICIENCY: member_efficiency}

    logger.debug(f"for party:{party.name}, {str(party_efficiency)}")

    return party_efficiency


def getAllPartiesEfficiencyByTag(graph, tag, num_of_laws_backward):
    logger.debug(f"params: tag={tag}, num_of_laws={num_of_laws_backward}")

    parties_efficiancy = dict()
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)

    if len(laws) > 0:
        for party in Party.select(graph=graph):
            parties_efficiancy[party.name] = _getPartyEfficiancy(graph=graph, party=party, laws=laws)

    logger.debug(f"Parties Efficiancy: {str(parties_efficiancy)}")

    return parties_efficiancy

# TODO debug smart
def getAllLawProposalPerParty(graph, tag, num_of_laws_backward):
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)
    proposed_by = [(e.name, list(e.member_of_party)[0].name) for law in laws for e in list(law.proposed_by)]

    total_num_of_laws = len(laws)
    all_proposals = dict()

    for party_name, names_vs_party in itertools.groupby(proposed_by, key=lambda tup: tup[1]):
        elected_list = [name for name, party in list(filter(lambda p: p[1] == party_name, proposed_by))]
        num_of_proposals = len(elected_list)
        elected_proposals = {name : len(list(group)) for name, group in itertools.groupby(sorted(elected_list))}
        all_proposals[party_name] = {NUM_OF_PROPOSALS:(num_of_proposals/float(total_num_of_laws)), ELECTED_PROPOSALS: elected_proposals}

    return all_proposals


def _getPartyAbsentFromLaws(graph, party, laws):
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

    for name in member_missing.keys():
        member_missing[name] = member_missing[name]/float(total_missing)

    party_missing = {PARTY_MISSING: total_missing/float(total), MEMBER_MISSING: member_missing}

    return party_missing


def absentFromVotes(graph, tag, num_of_laws_backward):
    laws = LawService.getNumOfLawsByTag(graph=graph, tag=tag, num_of_laws=num_of_laws_backward)

    parties_missing = dict()

    if len(laws) > 0:
        for party in Party.select(graph=graph):
            parties_missing[party.name] = _getPartyAbsentFromLaws(graph=graph, party=party, laws=laws)

    logger.debug(f"Parties absent: {str(parties_missing)}")

    return parties_missing


def createGeneralStats(num_of_laws_backward):
    graph = bolt_connect()
    file_path = os.path.join(pathlib.PurePath(__file__).parent, "Tags.txt")
    with open(file_path, "r") as tags_file:
        for tag_name in tags_file:
            party_efficiency = f"{PARTY_EFFICIENCY}_{tag_name}"
            law_proposals = f"{LAW_PROPOSAL}_{tag_name}"
            absent_stats = f"{ABSENT_STATS}_{tag_name}"

            if "All" in tag_name:
                tag_name = None

            raw_data_efficiency = json.dumps(getAllPartiesEfficiencyByTag(graph=graph, tag=tag_name, num_of_laws_backward=num_of_laws_backward))
            GeneralInfo.createGeneralInfo(graph=graph, type=party_efficiency, raw_data=raw_data_efficiency)

            raw_data_proposals = json.dumps(getAllLawProposalPerParty(graph=graph, tag=tag_name, num_of_laws_backward=num_of_laws_backward))
            GeneralInfo.createGeneralInfo(graph=graph, type=law_proposals, raw_data=raw_data_proposals)

            raw_data_absent = json.dumps(absentFromVotes(graph=graph, tag=tag_name, num_of_laws_backward=num_of_laws_backward))
            GeneralInfo.createGeneralInfo(graph=graph, type=absent_stats, raw_data=raw_data_absent)


def getGeneralStats(graph, type, tag):
    node_type = f"{type}_{tag}"
    data = GeneralInfo.safeSelect(graph=graph, type=node_type).raw_data
    return data







