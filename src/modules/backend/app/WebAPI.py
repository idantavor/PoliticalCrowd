from flask import Flask, request, jsonify
from google.auth.transport import requests
from google.oauth2 import id_token
from modules.backend.bl.UserService import isUserExist
from src.modules.backend.common.APIConstants import *
from src.modules.dal.GraphConnection import bolt_connect
from src.modules.dal.graphObjects.graphObjects import User, Party, ElectedOfficial, Law, Residency, JobCategory

app = Flask(__name__)
app.secret_key = "ThisIsNotThePassword"

graph = bolt_connect()
auth_cache = {}

@app.errorhandler(Exception)
def defaultHandler(error):
    app.logger.error(str(error))
    return Response.FAILED, Response.CODE_FAILED

def authenticate(token):
    try:
        if auth_cache[token] is not None and not auth_cache[token]:
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
        auth_cache[token] = False
        pass

# api functions for first time login -- begin

#@app.route("/getParties", methods=['GET'])
def getParties():
    app.logger.debug("got parties request")
    parties = Party.select(graph)
    parties_names = []
    for party in parties:
        parties_names.append(party.name)
    app.logger.debug("returning "+str(parties_names))
    return parties_names

#@app.route("/getResidencies", methods=['GET'])
def getResidencies():
    app.logger.debug("got elected officials request")
    residencies = Residency.select(graph)
    residencies_names = []
    for residency in residencies:
        residencies_names.append(residency.name)
    app.logger.debug("returning " + str(residencies_names))
    return residencies_names

#@app.route("/getJobCategories", methods=['GET'])
def getJobCategories():
    app.logger.debug("got elected officials request")
    job_categories = JobCategory.select(graph)
    job_categories_names = []
    for job_category in job_categories:
        job_categories_names.append(job_category.name)
    app.logger.debug("returning " + str(job_categories_names))
    return job_categories_names


@app.route("/getElectedOfficials", methods=['GET'])
def getElectedOfficials():
    app.logger.debug("got elected officials request")
    elected_officials = ElectedOfficial.select(graph)
    elected_official_names = []
    for elected_official in elected_officials:
        elected_official_names.append(elected_official.name)
    app.logger.debug("returning " + str(elected_official_names))
    return jsonify(elected_official_names)

@app.route("/getCategoryNames", methods=['GET'])
def getCategoryNames():
    return jsonify({
        "parties":getParties(),
        "residencies": getResidencies(),
        "job_categories": getJobCategories()
    })

# adding שמאל and ימין tags

@app.route("/register", methods=['POST'])
def register():
    app.logger.debug("got registration request")
    user_token = request.form.get(USER_TOKEN)
    #user_id = authenticate(user_token) need to be done
    user_id = user_token # temporary
    if isUserExist(graph, user_id):
        birth_year = request.form.get(BIRTH_YEAR)
        job = request.form.get(JOB)
        city = request.form.get(RESIDENCY)
        party = request.form.get(PARTY)
        involvement = InvolvementLevel[request.form.get(INVOLVEMENT_LEVEL)]

        user = User.createUser(graph= graph, token=user_token, birthYear=birth_year,
                               involvementLevel=involvement.value, residancy=city,
                               job=job, party=party)

        app.logger.debug("created user " + str(user))
    return jsonify("Success")

# api functions for first time login  --- end

# notification api function --- start

@app.route("/lawNotification", methods=['POST'])
def lawNotification():
    user_token = request.form.get(USER_TOKEN)
    if isUserExist(graph, user_token):
        # read new laws from somewhere
        return "1"
    else:
        raise Exception("ileagal operation")

@app.route("/lawVoteSubmit", methods=['POST'])
def lawVoteSubmit():
    user_token = request.form.get(USER_TOKEN)
    law_name = request.form.get(LAW_NAME)
    vote = request.form.get(VOTE)
    user = User.safeSelect(graph, user_token)
    law = Law.safeSelect(graph, law_name)
    if vote is VOTED_FOR:
        user.voted_for.add(law)
    elif vote is VOTED_AGAINST:
        user.voted_against.add(law)
    else:
        raise Exception("ileagal vote type")
    graph.push(user)
#
# Votes History Screen
# 1. get last 100 laws  -> get user token
#       return last 100 laws from the relevant severity :for each law {id, link, name, description, party, party member}.
#       from here he can vote for the law
# 2. get last 100 laws voted -> get user token
#       return last 100 laws the user voted for: for each law return {name, id, the user vote}
#       from here he can change his vote
# 3. get law statistics -> get law id | name, user token
#       return {all relevant statistics(by: age, party, job, living area)



#
# Personal Statistics Screen
# one API function - get user token and return:
# 1. relation to his own party
# 2. relation to all other parties
# 3. relation to all other users by age/party/job etc.
# 4. favourite party member statistics: the user relation to his favourite member
# 5.

app.run("127.0.0.1", 8080, debug=True)