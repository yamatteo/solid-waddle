from functools import wraps

from flask import redirect, render_template, request, session, url_for

from mysite.init import app
from mysite.models import MultipleResultsFound, NoResultFound, User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            User.query.filter_by(username=session.get('username')).one()
        except (AssertionError, NoResultFound, MultipleResultsFound) as err:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user = User.query.filter_by(username=session.get('username')).one()
            assert user.is_editor
        except (AssertionError, NoResultFound, MultipleResultsFound) as err:
            print("EDITOR LOGIN ERROR", err)
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user = User.query.filter_by(username=username).one()
            assert user.check_password(password)
            session['username'] = username
            session["user_is_editor"] = user.is_editor
            return redirect('/')
        except (AssertionError, NoResultFound, MultipleResultsFound) as err:
            print("LOGIN ERROR", err)
            return render_template('login.html', error='Invalid username or password.')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')