# from flask import Flask, request, session, redirect, url_for, render_template, flash
#
# app = Flask(__name__)
#
# @app.route("/register", method=['POST'])
# # register
#
#
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