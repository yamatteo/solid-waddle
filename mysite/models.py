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
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound, MultipleResultsFound

from mysite.init import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///general.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_editor = db.Column(db.Boolean, default=False, nullable=False)

    def check_password(self, password):
        return self.password == password

class Topic(db.Model):
    id = db.Column(db.String(8), primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    prerequisites = db.Column(db.String(255), nullable=False)

    def unfold(self):
        prerequisites = [ topic for topic in self.prerequisites.split(";__;") if len(topic) > 0 ]
        return Topic(
            id=self.id,
            title=self.title,
            description=self.description,
            prerequisites=prerequisites,
        )

class Problem(db.Model):
    id = db.Column(db.String(8), primary_key=True)
    topic_id = db.Column(db.String(8), db.ForeignKey('topic.id'), nullable=False)
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
    topic_id = db.Column(db.String(8), db.ForeignKey('topic.id'), nullable=False)
    problems_seen = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)

class TopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=80)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=255)])
    prerequisites = SelectMultipleField('Prerequisites', coerce=str)
    submit = SubmitField('Save Changes')

class ProblemForm(FlaskForm):
    topic_id = StringField('Topic ID', validators=[DataRequired()])
    text = TextAreaField('Text', validators=[DataRequired(), Length(max=255)])
    solutions = TextAreaField('Solutions', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Save Changes')

with app.app_context():
    db.create_all()

def export_users_to_csv(filename):        
    # Get all users from the database
    users = db.session.query(User).all()
    
    # Open the file for writing
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header row
        writer.writerow(['id', 'username', 'password'])
        
        # Write each user to the CSV file
        for user in users:
            writer.writerow([user.id, user.username, user.password])

def import_users_from_csv(filename, overwrite=False):        
    # If we're overwriting, delete all existing users
    if overwrite:
        db.session.query(User).delete()
    
    # Open the CSV file for reading
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Loop through each row in the CSV file
        for row in reader:
            # If the user already exists and we're not overwriting, skip this row
            try:
                user = db.session.query(User).filter_by(username=row['username']).first()
                if not overwrite and user is not None:
                    continue
            except OperationalError as err:
                print(err)
            
            # Create a new User object and set its properties
            user = User()
            user.username = row['username']
            user.password = row['password']
            
            # Add the user to the session
            db.session.add(user)
    
    # Commit the changes to the database
    db.session.commit()

def load_topics_from_json(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

        for topic_data in data['topics']:
            topic = Topic(
                id=topic_data['id'],
                title=topic_data['title'],
                description=topic_data['description'],
                prerequisites=','.join(topic_data['prerequisites'])
            )
            db.session.add(topic)
            # print("Adding", topic.title)

        db.session.commit()

def load_problems_from_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
        
        for problem_data in data['problems']:
            problem = Problem.query.get(problem_data['id'])
            
            if problem:
                problem.topic_id = problem_data['topic_id']
                problem.text = problem_data['text']
                problem.solutions = ','.join(problem_data['solutions'])
                db.session.merge(problem)
            else:
                problem = Problem(
                    id=problem_data['id'],
                    topic_id=problem_data['topic_id'],
                    text=problem_data['text'],
                    solutions=','.join(problem_data['solutions'])
                )
                db.session.add(problem)
        
        db.session.commit()