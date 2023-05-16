from functools import wraps

from flask import redirect, render_template, request, session, url_for

from mysite.init import app
from mysite.models import MultipleResultsFound, NoResultFound, User, db


from functools import update_wrapper

def login_required(student=False, teacher=False, editor=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user = User.query.filter_by(username=session.get('username')).one()
                if student and not user.is_student:
                    raise AssertionError("Access denied for non-student user")
                if teacher and not user.is_teacher:
                    raise AssertionError("Access denied for non-teacher user")
                if editor and not user.is_editor:
                    raise AssertionError("Access denied for non-editor user")
            except (AssertionError, NoResultFound, MultipleResultsFound) as err:
                print("LOGIN ERROR", err)
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        
        # Update the attributes of the inner function to match the original function
        update_wrapper(decorated_function, f)
        
        return decorated_function
    
    return decorator



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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        language = request.form['language']
        is_student = 'student' in request.form
        is_teacher = 'teacher' in request.form
        is_editor = 'editor' in request.form

        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match.')

        # Check if the username or email is already registered
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error='Username already exists. Please choose a different username.')

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template('signup.html', error='Email already exists. Please choose a different email.')

        # Create a new User instance
        new_user = User(email=email, username=username, password=password, language=language,
                        is_student=is_student, is_teacher=is_teacher, is_editor=is_editor)

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Redirect to the login page or any other appropriate page
        return redirect('/login')
    else:
        return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')
