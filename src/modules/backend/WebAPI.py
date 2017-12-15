from flask import Flask, request, jsonify
from flask import flash

from modules.dal.GraphConnection import bolt_connect
from src.modules import Logger
from src.modules.backend.APIConstants import *
from src.modules.dal.graphObjects.graphObjects import User, Party, ElectedOfficial

app = Flask(__name__)
app.secret_key = "ThisIsNotThePassword"
logger = Logger.getLogger("WebAPI", is_debug=True)
graph = bolt_connect()

@app.errorhandler(Exception)
def defaultHandler(error):
    logger.error(str(error))
#    if type(error   )
#        return 1
    return Response.FAILED, Response.CODE_FAILED

def isUserInSession(user):
    return 1

# api functions for first time login -- begin

@app.route("/getParties", methods=['GET'])
def getParties():

    parties = Party.select(graph)
    parties_names = []
    for party in parties:
        parties_names.append(party.name)
    return jsonify(parties_names)

@app.route("/getElectedOfficials", methods=['GET'])
def getElectedOfficials():
    elected_officials = ElectedOfficial.select(graph)
    elected_official_names = []
    for elected_official in elected_officials:
        elected_official_names.append(elected_official.name)
    return jsonify(elected_official_names)

# getResidancies like parties

# getJobCategories like parties

# adding שמאל and ימין tags

@app.route("/register", methods=['POST'])
def register():
    user_token = request.form.get(USER_TOKEN)
    birth_year = request.form.get(BIRTH_YEAR)
    job = request.form.get(JOB)
    city = request.form.get(RESIDANCY)
    party = request.form.get(PARTY)
    involvment = InvolvementLevel[request.form.get(INVOLVEMENT_LEVEL)]

    new_user = User.createUser(token=user_token, birthYear=birth_year,
                               involvmentLevel=involvment, residancy=city,
                               job=job)
    new_user.associate_party = Party.select(graph, primary_value=party).first()
    graph.begin(autocommit=True).push(new_user)
    return Response.SUCCESSS, Response.CODE_SUCCESS

# api functions for first time login  --- end

# notification api function --- start

app.run("127.0.0.1", 8080, debug=True)

# Notification Screen
# 1. law notification -> get user token, last update timestamp
#     return {id, link, name, description, party, party member, }
#
# 2.  law vote submit -> get user token, law name & id, vote
#     return {party members votes - his own party, other parties, etc.}
#
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
#
# Personal Statistics Screen
# one API function - get user token and return:
# 1. relation to his own party
# 2. relation to all other parties
# 3. relation to all other users by age/party/job etc.
# 4. favourite party member statistics: the user relation to his favourite member
# 5.