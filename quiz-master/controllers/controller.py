from calendar import c

from flask import Flask,request,render_template,url_for,redirect, flash,session,current_app as app,jsonify
from flask.globals import request_ctx
from flask_sqlalchemy.session import Session
from sqlalchemy import extract
from sqlalchemy.sql import func
from sqlalchemy.testing.suite.test_reflection import users

from models import db, User, Subject, Chapter, Quiz, Question, Score
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
import random

# Generic Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    if request.method=='GET':
        return render_template('login.html')

@app.route('/logout')
def logout():
    print('Logout')
    session.pop('user_id',None)
    return redirect(url_for('login'))

@app.route('/login',methods=['POST'])
def login_process():
    print('Login Process')
    userid = request.form['userid']
    passhash = request.form['password']
    user=User.query.filter_by(userid=userid).first()
    print("User Exists")
    if user:
        if check_password_hash(user.passhash,passhash):
            session['user_id'] = user.userid
            if user.userid=='admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Incorrect Password","error")
            return redirect(url_for('login'))
    else:
        flash("No User found with this User ID")
        return redirect(url_for('login'))

@app.route('/register')
def register():
    print("Register Requested")
    return render_template('register.html')


# User
# Backend Validation Already Done
@app.route('/register',methods=['POST'])
def register_user():
    print("Register Post Requested")
    userid = request.form['userid']
    name = request.form['name']
    passhash = generate_password_hash(request.form['password'])
    qualification = request.form['qualification']
    dob = request.form['dob']
    if userid == '' or passhash == '':
        print("Username or Password can not be Empty")
        flash('Username or Password can not be Empty')
        return redirect(url_for('register'))
    if qualification=='Select Qualification':
        print("Please Select Correct Qualification")
        flash('Please Select Correct Qualification')
        return redirect(url_for('register'))
    if User.query.filter_by(userid=userid).first():
        print("User Already Exists")
        flash('User with this username Already Exists, Please Choose another Username')
        return redirect(url_for('register'))
    user=User(userid=userid,name=name,passhash=passhash,qualification=qualification,dob=dob,created_on=datetime.now())
    db.session.add(user)
    db.session.commit()
    flash('User Successfully Registered.')
    print('User Successfully Registered.')
    return redirect(url_for('login'))


@app.route('/user/delete',methods=['POST','GET'])
def user_delete():
    user_id = request.args.get('user', type=int)
    print(user_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        db.session.delete(user)
        db.session.commit()
        flash('User Deleted Successfully')
        return redirect(url_for('admin_dashboard'))

    print(user)
    return render_template('user/delete_user.html', user_id=user_id, user=user)

@app.route('/userdashboard')
def user_dashboard():
    user_id=session.get('user_id')
    print(user_id)
    if user_id==None:
        flash('Please Login')
        return redirect(url_for('login'))
    if user_id=='admin':
        flash('Invalid Login')
        return redirect(url_for('admin_dashboard'))

    user=User.query.filter_by(userid=user_id).first()
    print(user)
    print("User Dashboard")
    print(session)
    print(datetime.today().strftime('%Y-%m-%d'))
    todays_date=datetime.today().strftime('%Y-%m-%d')
    quizzes=Quiz.query.filter(Quiz.date_of_quiz>=todays_date).all()
    scores=Score.query.filter_by(user_id=user_id).all()
    print(quizzes)
    attempted={""}
    for s in scores:
        attempted.add(s.quiz_id)
    return render_template('user/userDashboard.html',user=user,quizzes=quizzes,todays_date=todays_date,attempted=attempted)

@app.route('/userSummary')
def user_summary():
    user_id = session.get('user_id')
    user_quizzes = (
        db.session.query(
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            func.count(Score.id).label("quiz_count")
        )
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .join(Score, Score.quiz_id == Quiz.id)
        .filter(Score.user_id == user_id)
        .group_by(Subject.id, Subject.name)
        .order_by(func.count(Score.id).desc())
        .all()
    )
    user_scores = (
        db.session.query(
            Quiz.id.label("quiz_id"),
            Chapter.name.label("chapter"),
            Score.total_scored.label("total_scored"),
        )
        .join(Score, Score.quiz_id == Quiz.id)
        .join(Chapter, Chapter.id == Quiz.chapter_id)
        .filter(Score.user_id == user_id)
        .order_by(Score.time_stamp_of_attempt.desc())
        .all()
    )

    print(user_scores)
    print(user_quizzes)
    return render_template('user/summary.html',user_quizzes=user_quizzes,user_scores=user_scores)

@app.route('/userSearch',methods=['POST'])
def user_search():
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))
    if session.get('user_id')=='admin':
        flash('Invalid Request')
        return redirect(url_for('admin_dashboard'))

    param = request.form['param']
    search = "%{}%".format(param)
    todays_date=datetime.today().strftime('%Y-%m-%d')

    quizzes = (
        Quiz.query
        .join(Chapter)
        .filter(Chapter.name.ilike(f"%{search}%"))
        .filter(Quiz.date_of_quiz >= todays_date)
        .all()
    )
    subjects=Subject.query.filter(Subject.name.like(search)).all()

    print(users)
    print(subjects)
    print("User Search")
    return render_template('user/search.html',quizzes=quizzes,subjects=subjects)

# Admin

@app.route('/admindashboard')
def admin_dashboard():
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))
    if session.get('user_id')!='admin':
        flash('Invalid Request')
        return redirect(url_for('user_dashboard'))
    print("Admin Dashboard")
    subjects=Subject.query.all();
    return render_template('admin/adminDashboard.html',subjects=subjects)

@app.route('/adminSearch',methods=['POST'])
def admin_search():
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))
    if session.get('user_id')!='admin':
        flash('Invalid Request')
        return redirect(url_for('user_dashboard'))

    param = request.form['param']
    search = "%{}%".format(param)
    users=User.query.filter(User.name.like(search) , User.userid != 'admin').all()
    subjects=Subject.query.filter(Subject.name.like(search)).all()
    chapters=Chapter.query.filter(Chapter.name.like(search)).all()
    print(users)
    print(subjects)
    print(chapters)
    print("Admin Dashboard")
    return render_template('admin/search.html',chapters=chapters,users=users,subjects=subjects)

# User Details for Admin
@app.route('/userDetails')
def user_details():
    print("User Details")
    users=User.query.filter(User.userid != 'admin').all()
    return render_template('admin/userDetails.html',users=users)


@app.route('/adminSummary')
def admin_summary():
    if session.get('user_id')!='admin':
        flash('Invalid Request')
        return redirect(url_for('user_dashboard'))

    chapter_counts = (
        db.session.query(
            Subject.name.label("subject_name"),
            func.count(Chapter.id).label("chapter_count")
        )
        .outerjoin(Chapter, Chapter.subject_id == Subject.id)
        .group_by(Subject.id, Subject.name)
        .all()
    )

    quiz_attempts = (
        db.session.query(
            Chapter.id.label("chapter_id"),
            Chapter.name.label("chapter_name"),
            func.count(Score.id).label("attempt_count")
        )
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .join(Score, Score.quiz_id == Quiz.id)
        .group_by(Chapter.id, Chapter.name)
        .all()
    )

    print(chapter_counts)
    print(quiz_attempts)
    print("Admin Summary")
    return render_template('admin/summary.html',chapter_counts=chapter_counts,quiz_attempts=quiz_attempts)

# Subject

@app.route('/subject/add',methods=['POST','GET'])
def add_subject():
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    if request.method=='POST':
        flash('Subject Added Successfully')
        name = request.form['name']
        desc = request.form['desc']
        subject=Subject(name=name,desc=desc,created_on=datetime.now())
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('subject/add_subject.html')


@app.route('/subject/edit',methods=['POST','GET'])
def edit_subject():
    subject_id = request.args.get('subject', type=int)
    print(subject_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    subject = Subject.query.filter_by(id=subject_id).first()
    if not subject:
        flash("Subject not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        name = request.form['name']
        desc = request.form['desc']
        subject.name=name
        subject.desc=desc
        db.session.commit()
        flash('Subject Edited Successfully')
        return redirect(url_for('admin_dashboard'))
    print(subject)
    return render_template('subject/edit_subject.html',subject_id=subject_id,subject=subject)


@app.route('/subject/delete',methods=['POST','GET'])
def delete_subject():
    subject_id = request.args.get('subject', type=int)
    print(subject_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    subject = Subject.query.filter_by(id=subject_id).first()
    if not subject:
        flash("Subject not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        db.session.delete(subject)
        db.session.commit()
        flash('Subject Deleted Successfully')
        return redirect(url_for('admin_dashboard'))

    print(subject)
    return render_template('subject/delete_subject.html', subject_id=subject_id, subject=subject)

# Chapter

@app.route('/chapter/add',methods=['POST','GET'])
def add_chapter():
    subject_id = request.args.get('subject', default=1, type=int)
    print(subject_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    if request.method=='POST':
        flash('Subject Added Successfully')
        name = request.form['name']
        desc = request.form['desc']
        chapter=Chapter(name=name,desc=desc,created_on=datetime.now(),subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('chapter/add_chapter.html',subject_id=subject_id)

@app.route('/chapter/edit',methods=['POST','GET'])
def edit_chapter():
    chapter_id = request.args.get('chapter', type=int)
    print(chapter_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    chapter = Chapter.query.filter_by(id=chapter_id).first()
    if not chapter:
        flash("Chapter not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        name = request.form['name']
        desc = request.form['desc']
        chapter.name=name
        chapter.desc=desc
        db.session.commit()
        flash('Chapter Edited Successfully')
        return redirect(url_for('admin_dashboard'))
    print(chapter)
    return render_template('chapter/edit_chapter.html',chapter_id=chapter_id,chapter=chapter)

@app.route('/chapter/delete',methods=['POST','GET'])
def delete_chapter():
    chapter_id = request.args.get('chapter', type=int)
    print(chapter_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    chapter = Chapter.query.filter_by(id=chapter_id).first()
    if not chapter:
        flash("Chapter not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        db.session.delete(chapter)
        db.session.commit()
        flash('Chapter Deleted Successfully')
        return redirect(url_for('admin_dashboard'))

    print(chapter)
    return render_template('chapter/delete_chapter.html', chapter_id=chapter_id, chapter=chapter)

# Question

@app.route('/question/add',methods=['POST','GET'])
def add_question():
    quiz_id = request.args.get('quiz', default=1, type=int)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))
    quiz=Quiz.query.filter_by(id=quiz_id).first()
    if request.method=='POST':

        question_title = request.form['question_title']
        question_statement = request.form['question_statement']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']
        question=Question(quiz_id=quiz_id,question_title=question_title,question_statement=question_statement,option_1=option_1,option_2=option_2,option_3=option_3,option_4=option_4,correct_option=correct_option)
        db.session.add(question)
        db.session.commit()
        flash('Question Added Successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('question/add_question.html',quiz_id=quiz_id,quiz=quiz)

@app.route('/question/edit',methods=['POST','GET'])
def edit_question():
    question_id = request.args.get('question', type=int)
    print(question_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    question = Question.query.filter_by(id=question_id).first()
    if not question:
        flash("Question not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        question_title = request.form['question_title']
        question_statement = request.form['question_statement']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']

        question.question_title=question_title
        question.question_statement=question_statement
        question.option_1 = option_1
        question.option_2 = option_2
        question.option_3 = option_3
        question.option_4 = option_4
        question.correct_option = correct_option
        db.session.commit()
        flash('Question Edited Successfully')
        return redirect(url_for('quiz_dashboard'))
    print(question)
    return render_template('question/edit_question.html',question_id=question_id,question=question)

@app.route('/question/delete',methods=['POST','GET'])
def delete_question():
    question_id = request.args.get('question', type=int)
    print(question_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    question = Question.query.filter_by(id=question_id).first()
    if not question:
        flash("Question not found!")
        return redirect(url_for('quiz_dashboard'))

    if request.method=='POST':
        db.session.delete(question)
        db.session.commit()
        flash('Question Deleted Successfully')
        return redirect(url_for('quiz_dashboard'))

    print(question)
    return render_template('question/delete_question.html', question_id=question_id, question=question)


# Quiz

@app.route('/quizdashboard')
def quiz_dashboard():
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))
    print("Quiz Dashboard")
    quizzes=Quiz.query.all()
    return render_template('quiz/quizDashboard.html',quizzes=quizzes)



# Add Quiz
@app.route('/quiz/add',methods=['POST','GET'])
def add_quiz():
    chapter_id = request.args.get('chapter', type=int)
    if chapter_id=="":
        flash('Invalid Chapter ID')
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))
    chapter = Chapter.query.filter_by(id=chapter_id).first()

    if request.method=='POST':
        chapter_id = request.form['chapter']
        date = request.form['date']
        hours = request.form['hours']
        minutes = request.form['minutes']
        max_marks = request.form['max_marks']
        quiz=Quiz(chapter_id=chapter_id,date_of_quiz=date,hour_duration=hours,min_duration=minutes,max_marks=max_marks)
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz Added Successfully')
        return redirect(url_for('quiz_dashboard'))


    return render_template('quiz/add_quiz.html',chapter=chapter)

@app.route('/quiz/edit',methods=['POST','GET'])
def edit_quiz():
    quiz_id = request.args.get('quiz', type=int)
    print(quiz_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        flash("Quiz not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method=='POST':
        date = request.form['date']
        hours = request.form['hours']
        minutes = request.form['minutes']
        marks= request.form['max_marks']
        print(date)
        quiz.date_of_quiz=date
        quiz.max_marks=marks
        quiz.hour_duration=hours
        quiz.min_duration=minutes
        db.session.commit()
        flash('Quiz Edited Successfully')
        return redirect(url_for('quiz_dashboard'))
    print(quiz)
    return render_template('quiz/edit_quiz.html',quiz_id=quiz_id,quiz=quiz)

@app.route('/quiz/delete',methods=['POST','GET'])
def delete_quiz():
    quiz_id = request.args.get('quiz', type=int)
    print(quiz_id)
    if session.get('user_id')==None:
        flash('Please Login')
        return redirect(url_for('login'))

    if session.get('user_id')!='admin':
        flash('Only Admins Can Access this Page')
        return redirect(url_for('user_dashboard'))

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        flash("Quiz not found!")
        return redirect(url_for('quiz_dashboard'))

    if request.method=='POST':
        db.session.delete(quiz)
        db.session.commit()
        flash('Quiz Deleted Successfully')
        return redirect(url_for('quiz_dashboard'))

    print(quiz)
    return render_template('quiz/delete_quiz.html', quiz_id=quiz_id, quiz=quiz)


@app.route('/quiz/attempt',methods=['POST','GET'])
def attempt_quiz():
    print(request.method)
    quiz_id = request.args.get('quiz', type=int)
    quiz=Quiz.query.filter_by(id=quiz_id).first()
    random.shuffle(quiz.questions)

    if request.method=='POST':
        qscore=0;
        for i in quiz.questions:
            qid="q"+str(i.id)
            input=request.form.get(qid)
            question=Question.query.filter_by(id=i.id).first()
            if(input==question.correct_option):
                qscore+=1;
        userid=session['user_id']
        scr=quiz.max_marks/len(quiz.questions) * qscore
        score=Score(quiz_id=quiz_id,total_scored=scr,user_id=userid,time_stamp_of_attempt=datetime.now())
        db.session.add(score)
        db.session.commit()
        flash('Quiz Attempted')
        return redirect(url_for('user_scores'))

    return render_template('quiz/attempt.html',quiz=quiz,quiz_id=quiz_id)

@app.route('/quiz/view')
def view_quiz():
    quiz_id = request.args.get('quiz', type=int)
    quiz=Quiz.query.filter_by(id=quiz_id).first()

    return render_template('quiz/view.html',quiz=quiz)

@app.route('/user/scores')
def user_scores():
    user=session['user_id']
    scores=Score.query.filter_by(user_id=user).all()

    return render_template('scores/view.html',scores=scores)


# APIs

@app.route('/getAllSubjects')
def get_all_subjects():
    subjects=Subject.query.all()
    print(subjects)
    return jsonify([{"id": s.id, "name": s.name, "desc": s.desc,"created_on":s.created_on} for s in subjects])

@app.route('/getSubjectById')
def get_subjects_by_id():
    subject_id = request.args.get('subject', type=int)
    subjects=Subject.query.filter_by(id=subject_id)
    print(subjects)
    return jsonify([{"id": s.id, "name": s.name, "desc": s.desc,"created_on":s.created_on} for s in subjects])

@app.route('/getAllChapters')
def get_all_chapters():
    chapters=Chapter.query.all()
    print(chapters)
    return jsonify([{"id": c.id, "name": c.name,"subject": c.subject_id, "desc": c.desc,"created_on":c.created_on} for c in chapters])

@app.route('/getChapterById')
def get_chapter_by_id():
    chapter_id = request.args.get('chapter', type=int)
    chapters=Chapter.query.filter_by(id=chapter_id)
    print(chapters)
    return jsonify([{"id": c.id, "name": c.name,"subject": c.subject_id, "desc": c.desc,"created_on":c.created_on} for c in chapters])


@app.route('/getAllQuizzes')
def get_all_quizzes():
    quizzes=Quiz.query.all()
    print(quizzes)
    return jsonify([{"id": q.id, "chapter_id": q.chapter_id,"date_of_quiz": q.date_of_quiz, "hour_duration": q.hour_duration,"min_duration":q.min_duration,"max_marks":q.max_marks} for q in quizzes])

@app.route('/getQuizById')
def get_quiz_by_id():
    quiz_id = request.args.get('quiz', type=int)
    quizzes=Quiz.query.filter_by(id=quiz_id)
    print(quizzes)
    return jsonify([{"id": q.id, "chapter_id": q.chapter_id,"date_of_quiz": q.date_of_quiz, "hour_duration": q.hour_duration,"min_duration":q.min_duration,"max_marks":q.max_marks} for q in quizzes])


@app.route('/getAllScores')
def get_all_scores():
    scores=Score.query.all()
    print(scores)
    return jsonify([{"id": s.id,"quiz_id": s.quiz_id, "user_id": s.user_id,"total_scored":s.total_scored,"time_stamp_of_attempt":s.time_stamp_of_attempt} for s in scores])

@app.route('/getScoreById')
def get_score_by_id():
    quiz_id = request.args.get('quiz', type=int)
    scores=(Score.query
            .join(Quiz)
            .filter(Quiz.id == quiz_id))
    print(scores)
    return jsonify([{"id": s.id,"quiz_id": s.quiz_id, "user_id": s.user_id,"total_scored":s.total_scored,"time_stamp_of_attempt":s.time_stamp_of_attempt} for s in scores])
