from flask import Flask, request, jsonify
from google.auth.transport import requests
from google.oauth2 import id_token

from src.modules.backend.bl import LawService, ProfileService, PartyService, UserService
from src.modules.backend.common.APIConstants import *
from src.modules.dal.GraphConnection import bolt_connect
from src.modules.dal.graphObjects.graphObjects import User, Party, ElectedOfficial, Law, Residency, JobCategory
from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__)
app.secret_key = "ThisIsNotThePassword"

graph = bolt_connect()
auth_cache = SimpleCache()

@app.errorhandler(Exception)    
def defaultHandler(error):
    app.logger.error(str(error))
    return Response.FAILED, Response.CODE_FAILED

def authenticate(token):
    #temporary
    return token

    try:
        if auth_cache.get(token) is not None and not auth_cache(token):
            raise ValueError('Illeagal Token')
        idinfo = id_token.verify_firebase_token(token, requests.Request())

        # need to validate request came from our app
        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        return idinfo['sub']
    except ValueError:
        # Invalid token
        app.logger.error("Invalid Token recieved")
        auth_cache.set(token, False, timeout=15 * 60)
        pass


def getUsersId(request):
    user_token = request.form.get(USER_TOKEN)
    return authenticate(user_token)

# api functions for first time login -- begin

def getParties():
    app.logger.debug("got parties request")
    parties = Party.select(graph)
    parties_names = []
    for party in parties:
        parties_names.append(party.name)
    app.logger.debug("returning "+str(parties_names))
    return parties_names

def getResidencies():
    app.logger.debug("got elected officials request")
    residencies = Residency.select(graph)
    residencies_names = []
    for residency in residencies:
        residencies_names.append(residency.name)
    app.logger.debug("returning " + str(residencies_names))
    return residencies_names

def getJobCategories():
    app.logger.debug("got elected officials request")
    job_categories = JobCategory.select(graph)
    job_categories_names = []
    for job_category in job_categories:
        job_categories_names.append(job_category.name)
    app.logger.debug("returning " + str(job_categories_names))
    return job_categories_names


@app.route("/getElectedOfficials", methods=['POST'])
def getElectedOfficials():
    app.logger.debug("got elected officials request")
    getUsersId(request)
    elected_officials = ElectedOfficial.select(graph)
    elected_official_names = []
    for elected_official in elected_officials:
        elected_official_names.append(elected_official.name)
    app.logger.debug("returning " + str(elected_official_names))
    return jsonify(elected_official_names)

@app.route("/getCategoryNames", methods=['POST'])
def getCategoryNames():
    app.logger.debug("categories request recieved")
    getUsersId(request)
    return jsonify({
        "parties":getParties(),
        "residencies": getResidencies(),
        "job_categories": getJobCategories()
    })

# adding שמאל and ימין tags

@app.route("/register", methods=['POST'])
def register():
    app.logger.info("got registration request")
    user_id = getUsersId(request)
    if not UserService.isUserExist(graph, user_id):
        birth_year = request.form.get(BIRTH_YEAR)
        job = request.form.get(JOB)
        city = request.form.get(RESIDENCY)
        party = request.form.get(PARTY)
        involvement = InvolvementLevel[request.form.get(INVOLVEMENT_LEVEL)]

        user = User.createUser(graph= graph, token=user_id, birthYear=birth_year,
                               involvementLevel=involvement.value, residancy=city,
                               job=job, party=party)

        app.logger.debug("created user " + str(user))
    return jsonify("Success")



# General Statistics

def validTags(tag):
    if tag is None:
        raise Exception("Missing tags")


    return tag


@app.route("/getAllPartiesEfficiency", methods=['POST'])
def allPartiesEfficiency():
    getUsersId(request)
    return jsonify(PartyService.getGeneralStats(graph = graph, tag=PartyService.ALL,type=PartyService.PARTY_EFFICIENCY))


@app.route("/getAllPartiesEfficiencyByTag", methods=['POST'])
def allPartiesEfficiencyByTag():
    getUsersId(request)
    tag = validTags(request.form.get(TAGS))
    return jsonify(PartyService.getGeneralStats(graph = graph, tag=tag, type=PartyService.PARTY_EFFICIENCY))

@app.route("/getAllLawProposals", methods=['POST'])
def allLawProposals():
    getUsersId(request)
    return jsonify(PartyService.getGeneralStats(graph=graph, tag=PartyService.ALL, type=PartyService.LAW_PROPOSAL))

@app.route("/getAllLawProposalsByTag", methods=['POST'])
def allLawProposalsByTag():
    getUsersId(request)
    tag = validTags(request.form.get(TAGS))
    return jsonify(PartyService.getGeneralStats(graph = graph, tag=tag, type=PartyService.LAW_PROPOSAL))

@app.route("/getAllAbsentFromVotes", methods=['POST'])
def allAbsentFromVotes():
    getUsersId(request)
    return jsonify(PartyService.getGeneralStats(graph = graph, tag=PartyService.ALL, type=PartyService.ABSENT_STATS))

@app.route("/getAllAbsentFromVotesByTag", methods=['POST'])
def allAbsentFromVotesByTag():
    getUsersId(request)
    tag = validTags(request.form.get(TAGS))
    return jsonify(PartyService.getGeneralStats(graph=graph, tag=tag, type=PartyService.ABSENT_STATS))


# Personal Statistics

def validNumberOfLaws(num):
    if num is None or num not in [1, 10, 100]:
        raise Exception("Invalid number of laws")
    return num

def validElectedOfficial(elected_official):
    if elected_official is None:
        raise Exception("Missing elected_official")
    return elected_official


@app.route("/getUserPartiesVotesMatch", methods=['POST'])
def usersPartyMatch():
    user_id = getUsersId(request)
    return jsonify(UserService.getUserPartiesVotesMatchByTag(graph = graph, user_id=user_id, tag=None))

@app.route("/getUserPartiesVotesMatchByTag", methods=['POST'])
def userPartiesVotesMatchByTag():
    user_id = getUsersId(request)
    tag = validTags(request.form.get(TAGS))
    return jsonify(UserService.getUserPartiesVotesMatchByTag(graph = graph, user_id=user_id, tag=tag))


@app.route("/getUserToElectedOfficialMatch", methods=['POST'])
def userToElectedOfficialMatch():
    user_id = getUsersId(request)
    elected_official = ElectedOfficial.safeSelect(validElectedOfficial(request.form.get(ELECTED_OFFICIAL)))
    return jsonify(UserService.getUserMatchForOfficial(graph=graph, user_id=user_id, member_name=elected_official, tag=None))

@app.route("/getUserToElectedOfficialMatchByTag", methods=['POST'])
def userToElectedOfficialMatchByTag():
    user_id = getUsersId(request)
    tag = validTags(request.form.get(TAGS))
    elected_official = ElectedOfficial.safeSelect(validElectedOfficial(request.form.get(ELECTED_OFFICIAL)))
    return jsonify(
        UserService.getUserMatchForOfficial(graph=graph, user_id=user_id, member_name=elected_official, tag=tag))

# Laws

@app.route("/getLawsByDateInterval", methods=['POST'])
def lawsByDateInterval():
    getUsersId(request)
    start_date = request.form.get(START_DATE)
    end_date = request.form.get(END_DATE)
    return jsonify(LawService.getLawsByDateInterval(graph = graph, start_date = start_date, end_date = end_date))



@app.route("/lawNotification", methods=['POST'])
def lawNotification():
    app.logger.info("law notification request recieved")
    user_id = getUsersId(request)
    return jsonify(LawService.getNewLaws(graph=graph, user_id=user_id))

# Laws Actions

@app.route("/lawVoteSubmit", methods=['POST'])
def lawVoteSubmit():
    user_id = getUsersId(request)
    app.logger.info("recieved request for vote from ["+str(user_id)+"]")
    law_name = request.form.get(LAW_NAME)
    vote = request.form.get(VOTE)
    tags = request.form.get(TAGS).split(",")

    LawService.submitVoteAndTags(graph, law_name, tags, user_id, vote)

    law_stats = LawService.getElectedOfficialLawStats(graph=graph, law_name=law_name, user_vote=vote, user_id=user_id)

    return jsonify(law_stats)


#Profile

@app.route("/updatePersonalInfo", methods=['POST'])
def updatePersonalInfo():
    user_id = getUsersId(request)
    app.logger.info("recieved request to update presonal info from [" + str(user_id) + "]")
    job = request.form.get(JOB)
    residency = request.form.get(RESIDENCY)
    party = request.form.get(PARTY)
    involvement_level = request.form.get(INVOLVEMENT_LEVEL)
    ProfileService.updatePersonlInfo(graph = graph, user_id=user_id, job = job, residency = residency, party = party, involvement_level = involvement_level)
    return jsonify("Success")


app.run("127.0.0.1", 8080, debug=True)