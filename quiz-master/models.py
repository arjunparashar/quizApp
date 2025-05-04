from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import nulls_last
from sqlalchemy.orm import backref
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash,check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    qualification = db.Column(db.String(64), nullable=True)
    dob = db.Column(db.String(64), nullable=True)
    created_on = db.Column(db.Date)

    def serialize(self):
        return {"id": self.id,
                "userid": self.userid,
                "name": self.name}

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    desc = db.Column(db.String(255), nullable=True)
    created_on=db.Column(db.Date)
    chapters = db.relationship('Chapter', backref='subject', cascade='all, delete-orphan', lazy=True)


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete="CASCADE"),nullable=False)
    desc = db.Column(db.String(255), nullable=True)
    created_on = db.Column(db.Date)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete="CASCADE"))
    chapter = db.relationship("Chapter", backref="chapter", uselist=False)
    date_of_quiz = db.Column(db.String(255), nullable=True)
    hour_duration = db.Column(db.String(255), nullable=True)
    min_duration = db.Column(db.String(255), nullable=True)
    max_marks = db.Column(db.Integer, nullable=True)
    questions=db.relationship("Question", backref='quiz', lazy=True)
    scores = db.relationship("Score", backref='score', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete="CASCADE"))
    question_title = db.Column(db.String(255), nullable=True)
    question_statement = db.Column(db.String(255), nullable=True)
    option_1 = db.Column(db.String(255), nullable=True)
    option_2 = db.Column(db.String(255), nullable=True)
    option_3 = db.Column(db.String(255), nullable=True)
    option_4 = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(255), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete="CASCADE"))
    quiz = db.relationship("Quiz", backref="quiz", uselist=False, viewonly=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    user = db.relationship("User", backref="user", uselist=False)
    time_stamp_of_attempt = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    total_scored = db.Column(db.String(64), nullable=False)