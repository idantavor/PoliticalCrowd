import logging

from modules.backend.common.APIConstants import InvolvementLevel
from modules.dal.graphObjects.graphObjects import User

logger = logging.getLogger(__name__)

def updateExistingField(graph, update_function, new_value):
    if new_value is not None:
        update_function(graph, new_value)


def updatePersonlInfo(graph, user_id, job, residency, party, involvement_level):
    user = User.safeSelect(graph, user_id)
    updateExistingField(graph=graph, update_function=user.changeJobField, new_value=job)
    updateExistingField(graph=graph, update_function=user.changeResidency, new_value=residency)
    updateExistingField(graph=graph, update_function=user.changeAssociateParty, new_value=party)
    if involvement_level is not None:
        involvement_level = InvolvementLevel[involvement_level]
        updateExistingField(graph=graph, update_function=user.changeInvlovmentLevel, new_value=involvement_level)
