from flask import Flask, request, session, redirect, url_for, render_template, flash

app = Flask(__name__)

@app.route("/register", method=['POST'])
# register


#Notification Screen
1. law notification -> get user token, last update timestamp
    return {link, name, description, party, party member, }

2.  law vote submit -> get user token, law name, vote
    return {party members votes - his own party, other parties, etc.}

3.