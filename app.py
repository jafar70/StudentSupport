from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from flask_socketio import SocketIO, emit
import uuid
from flask_pymongo import PyMongo
import bcrypt
import os
from functools import wraps
from forms import ContactForm
from flask_mail import Message, Mail
import os 
import copy
import flask
import json
import random

# create the application object
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'

mail = Mail()

app = Flask(__name__)

app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfzBxAUAAAAAJLjFD_vn26-TnmC7G7IcVndrwJl'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfzBxAUAAAAAHB4KVHdlwhw7xPoAlCu9y0y4p3o'
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'lordjammar7@gmail.com'
app.config["MAIL_PASSWORD"] = 'osalami20'
mail.init_app(app)

socketio = SocketIO(app)
app.secret_key = 'my precious'

app.config['MONGO_DBNAME'] = 'login-flask'
app.config['MONGO_URI'] = 'mongodb://salamij:Osalami20_@ds139959.mlab.com:39959/login-flask'

mongo = PyMongo(app)

# use decorators to link the function to a url
@app.route('/')
def home():
    return render_template('index.html')  # render a template

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')  # render a template
    
@app.route('/faqs')
def faqs():
    return render_template('faqs.html')  # render a template
    
@app.route('/timetable')
def timetable():
    if 'username' in session:
        return render_template('timetable.html')

    return render_template('login.html')

    
@app.route('/availability')
def availability():
    if 'username' in session:
        return render_template('availability.html')

    return render_template('login.html')


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


@app.route('/user_login')
def user_login():
    if 'username' in session:
        flash('You were logged in.')
        return render_template('availability.html')

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    error = None
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
            session['username'] = request.form['username']
            return redirect(url_for('user_login'))

    error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('user_login'))
        
        error = 'That username already exists!'
        return render_template('register.html', error=error)

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You were logged out.')
    return redirect(url_for('home'))
   
messages = [{'text': 'Booting system', 'name': 'Bot'},
            {'text': 'Student Support Chat now live!', 'name': 'Bot'}]

users = {}


@socketio.on('connect', namespace='/iss')
def makeConnection():
    session['uuid'] = uuid.uuid1()
    session['username'] = 'New user'
    print('connected')
    users[session['uuid']] = {'username': 'New user'}
    
    for message in messages:
        print(message)
        emit('message', message)
    

@socketio.on('message', namespace='/iss')
def new_message(message):
    tmp = {'text': message, 'name': users[session['uuid']]['username']}
    print(tmp)
    messages.append(tmp)
    emit('message', tmp, broadcast=True)

@socketio.on('identify', namespace='/iss')
def on_identify(message):
    print('identify ' + message)
    users[session['uuid']] = {'username': message}
    

@app.route('/livechat')
def mainIndex():
    return render_template('livechat.html') 
    
@app.route('/contact', methods=['GET', 'POST'])
def contact():
  form = ContactForm()

  if request.method == 'POST':
    if form.validate() == False:
      flash('All fields are required.')
      return render_template('contact.html', form=form)
    else:
      msg = Message(form.subject.data, sender='contact@example.com', recipients=['your_email@example.com'])
      msg.body = """
      From: %s <%s>
      %s
      """ % (form.name.data, form.email.data, form.message.data)
      mail.send(msg)

      return render_template('contact.html', success=True)

  elif request.method == 'GET':
    return render_template('contact.html', form=form)

# start the server
if __name__ == '__main__':
        socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)