import os
from flask import Flask, render_template, redirect, url_for,request
from werkzeug.security import generate_password_hash

from models import db, User

app = Flask(__name__, instance_relative_config=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.secret_key = "0000000000"
db.init_app(app)

app.app_context().push()

with app.app_context():
    db.create_all()

if not User.query.filter_by(userid='admin').first():
    print("No Admin Registered")
    user = User(userid='admin', name='Admin', passhash=generate_password_hash('admin'), qualification="Admin's Qualification", dob='01/01/1970')
    db.session.add(user)
    db.session.commit()
    print("Admin Registered Successfully")

from controllers.controller import *

if __name__ == '__main__':
    app.run(debug = True)