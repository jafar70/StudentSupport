from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from flask_socketio import SocketIO, emit
import uuid
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
app.config["MAIL_USERNAME"] = 'jsalami60@gmail.com'
app.config["MAIL_PASSWORD"] = 'osalami20'

mail.init_app(app)

socketio = SocketIO(app)
app.secret_key = 'my precious'

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
    
@app.route('/timetable')
@login_required
def timetable():
    return render_template('timetable.html')  # render a template
    
@app.route('/availability')
@login_required
def availability():
    return render_template('availability.html')  # render a template

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

messages = [{'text': 'Booting system', 'name': 'Bot'},
            {'text': 'ISS Chat now live!', 'name': 'Bot'}]

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
@login_required
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
