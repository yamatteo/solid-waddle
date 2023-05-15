import csv
from io import StringIO
import json
from types import SimpleNamespace
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound
import sqlalchemy.exc

def initialize_database(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///general.db'
    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(80), nullable=False)
        is_editor = db.Column(db.Boolean, default=False, nullable=False)
        scores = db.relationship('Score', backref='user', lazy=True)

        def check_password(self, password):
            return self.password == password

    class Topic(db.Model):
        id = db.Column(db.String(8), primary_key=True)
        title = db.Column(db.String(80), nullable=False)
        description = db.Column(db.String(255), nullable=False)
        prerequisites = db.Column(db.String(255), nullable=False)
        scores = db.relationship('Score', backref='topic', lazy=True)

    class Problem(db.Model):
        id = db.Column(db.String(8), primary_key=True)
        topic_id = db.Column(db.String(8), db.ForeignKey('topic.id'), nullable=False)
        text = db.Column(db.String(255), nullable=False)
        solutions = db.Column(db.String(255), nullable=False)

    class Score(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        topic_id = db.Column(db.String(8), db.ForeignKey('topic.id'), nullable=False)
        problems_seen = db.Column(db.Integer, default=0)
        correct_answers = db.Column(db.Integer, default=0)
    
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
                except sqlalchemy.exc.OperationalError as err:
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

    
    return SimpleNamespace(**locals())