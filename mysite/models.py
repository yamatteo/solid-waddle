import csv
import json
from types import SimpleNamespace

import sqlalchemy.exc
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import (SelectMultipleField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import DataRequired, Length
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from mysite.init import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///general.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    language = db.Column(db.String(20), default="en", nullable=False)
    is_student = db.Column(db.Boolean, default=True, nullable=False)
    is_teacher = db.Column(db.Boolean, default=False, nullable=False)
    is_editor = db.Column(db.Boolean, default=False, nullable=False)

    def check_password(self, password):
        return self.password == password


class Topic(db.Model):
    id = db.Column(db.String(8), primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    prerequisites = db.Column(db.String(255), nullable=False)

    def unfold(self):
        prerequisites = [topic for topic in self.prerequisites.split(
            ";__;") if len(topic) > 0]
        return Topic(
            id=self.id,
            title=self.title,
            description=self.description,
            prerequisites=prerequisites,
        )


class Problem(db.Model):
    id = db.Column(db.String(8), primary_key=True)
    topic_id = db.Column(db.String(8), db.ForeignKey(
        'topic.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    solutions = db.Column(db.String(255), nullable=False)

    def unfold(self):
        return SimpleNamespace(
            id=self.id,
            topic_id=self.topic_id,
            text=self.text,
            solutions=self.solutions.split(";__;")
        )


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.String(8), db.ForeignKey(
        'topic.id'), nullable=False)
    problems_seen = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)


class TopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=80)])
    description = TextAreaField('Description', validators=[
                                DataRequired(), Length(max=255)])
    prerequisites = SelectMultipleField('Prerequisites', coerce=str)
    submit = SubmitField('Save Changes')


class ProblemForm(FlaskForm):
    topic_id = StringField('Topic ID', validators=[DataRequired()])
    text = TextAreaField('Text', validators=[DataRequired(), Length(max=255)])
    solutions = TextAreaField('Solutions', validators=[
                              DataRequired(), Length(max=255)])
    submit = SubmitField('Save Changes')


with app.app_context():
    db.create_all()


def export_data(filepath):
    # Export User table
    users = User.query.all()
    user_data = [
        {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'language': user.language,
            'is_student': user.is_student,
            'is_teacher': user.is_teacher,
            'is_editor': user.is_editor
        }
        for user in users
    ]

    # Export Topic table
    topics = Topic.query.all()
    topic_data = [
        {
            'id': topic.id,
            'title': topic.title,
            'description': topic.description,
            'prerequisites': topic.prerequisites.split(";__;") if topic.prerequisites else []
        }
        for topic in topics
    ]

    # Export Problem table
    problems = Problem.query.all()
    problem_data = [
        {
            'id': problem.id,
            'topic_id': problem.topic_id,
            'text': problem.text,
            'solutions': problem.solutions.split(";__;") if problem.solutions else []
        }
        for problem in problems
    ]

    # Export Score table
    scores = Score.query.all()
    score_data = [
        {
            'id': score.id,
            'user_id': score.user_id,
            'topic_id': score.topic_id,
            'problems_seen': score.problems_seen,
            'correct_answers': score.correct_answers
        }
        for score in scores
    ]

    # Create a dictionary to hold all the data
    data = {
        'users': user_data,
        'topics': topic_data,
        'problems': problem_data,
        'scores': score_data
    }

    # Save the data to a JSON file
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

    print("Data exported successfully.")


def import_data(filepath):
    # Load data from JSON file
    with open(filepath, 'r') as file:
        data = json.load(file)

    # Import User table data
    user_data = data.get('users', [])
    for user in user_data:
        new_user = User(
            email=user['email'],
            username=user['username'],
            password=user['password'],
            language=user['language'],
            is_student=user['is_student'],
            is_teacher=user['is_teacher'],
            is_editor=user['is_editor']
        )
        db.session.add(new_user)

    # Import Topic table data
    topic_data = data.get('topics', [])
    for topic in topic_data:
        new_topic = Topic(
            id=topic['id'],
            title=topic['title'],
            description=topic['description'],
            prerequisites=';__;'.join(topic['prerequisites'])
        )
        db.session.add(new_topic)

    # Import Problem table data
    problem_data = data.get('problems', [])
    for problem in problem_data:
        new_problem = Problem(
            id=problem['id'],
            topic_id=problem['topic_id'],
            text=problem['text'],
            solutions=';__;'.join(problem['solutions'])
        )
        db.session.add(new_problem)

    # Import Score table data
    score_data = data.get('scores', [])
    for score in score_data:
        new_score = Score(
            user_id=score['user_id'],
            topic_id=score['topic_id'],
            problems_seen=score['problems_seen'],
            correct_answers=score['correct_answers']
        )
        db.session.add(new_score)

    # Commit the changes to the database
    db.session.commit()

    print("Data imported successfully.")
