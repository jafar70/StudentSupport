from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from functools import wraps
import sqlite3
import os 
import copy
import flask
import json
import os
import random

# create the application object
app = flask.Flask(__name__)

# config
app.secret_key = 'my precious'
app.database = 'sample.db'

quiz_dir = 'quizzes'

quizzes = {}
for quiz in os.listdir(quiz_dir):
    print 'Loading', quiz
    quizzes[quiz] = json.loads(open(os.path.join(quiz_dir, quiz)).read())

@app.route('/Quiz')
def index():
    return flask.render_template('quizHome.html', quiz_names=zip(quizzes.keys(), map(lambda q: q['name'], quizzes.values())))

@app.route('/quiz/<id>')
def quiz(id):
    if id not in quizzes:
        return flask.abort(404)
    quiz = copy.deepcopy(quizzes[id])
    questions = list(enumerate(quiz["questions"]))
    random.shuffle(questions)
    quiz["questions"] = map(lambda t: t[1], questions)
    ordering = map(lambda t: t[0], questions)

    return flask.render_template('quiz.html', id=id, quiz=quiz, quiz_ordering=json.dumps(ordering))

@app.route('/check_quiz/<id>', methods=['POST'])
def check_quiz(id):
    ordering = json.loads(flask.request.form['ord'])
    quiz = copy.deepcopy(quizzes[id])
    print flask.request.form
    quiz['questions'] = sorted(quiz['questions'], key=lambda q: ordering.index(quiz['questions'].index(q)))
    print quiz['questions']
    answers = dict( (int(k), quiz['questions'][int(k)]['options'][int(v)]) for k, v in flask.request.form.items() if k != 'ord' )

    print answers

    if not len(answers.keys()):
        return flask.redirect(flask.url_for('quiz', id=id))

    for k in xrange(len(ordering)):
        if k not in answers:
            answers[k] = [None, False]

    answers_list = [ answers[k] for k in sorted(answers.keys()) ]
    number_correct = len(filter(lambda t: t[1], answers_list))

    return flask.render_template('check_quiz.html', quiz=quiz, question_answer=zip(quiz['questions'], answers_list), correct=number_correct, total=len(answers_list))


# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap


# use decorators to link the function to a url
@app.route('/')
def home():
    return render_template('index.html')  # render a template

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')  # render a template
    
@app.route('/faqs')
def faqs():
    return render_template('faqs.html')  # render a template
    
@app.route('/availability')
@login_required
def availability():
    return render_template('availability.html')  # render a template

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if (request.form['username'] != 'admin') \
                or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            flash('You were logged in.')
            return redirect(url_for('availability'))
    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.')
    return redirect(url_for('welcome'))
    

# connect to database
def connect_db():
    return sqlite3.connect(app.database)

if __name__ == '__main__':
    app.debug = True
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('IP', '0.0.0.0')
    app.run(port=port, host=host)    