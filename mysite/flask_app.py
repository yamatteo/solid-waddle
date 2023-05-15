from random import shuffle
import random

from flask import (abort, flash, redirect, render_template, request, session,
                   url_for)
from sqlalchemy.sql import func
from mysite.authentication import editor_required, login_required
from mysite.init import app
from mysite.models import (MultipleResultsFound, NoResultFound, Problem, Topic, TopicForm,
                           User, db)
from mysite.crud_problem import *
from mysite.crud_topic import *
import mysite.models


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/problems')
# @login_required
# def problem_list():
#     topics = Topic.query.all()
#     for topic in topics:
#         problems = Problem.query.filter_by(topic_id=topic.id).all()
#         topic.problems = problems
#     return render_template('problems.html', topics=topics)

@app.route('/problem/<problem_id>')
@login_required
def problem(problem_id):
    # Retrieve the problem with the given ID
    problem = Problem.query.get(problem_id)

    # Parse the solutions string into a list
    solutions = problem.solutions.split(',')
    shuffle(solutions)

    # Render the problem page template with the problem and solutions data
    return render_template('problem.html', problem=problem.unfold(), solutions=solutions)

@app.route('/random_problem/<topic_id>')
@login_required
def random_problem(topic_id):
    # Retrieve the problem with the given ID
    # topic = Topic.query.get(topic_id)
    problem = Problem.query.filter_by(topic_id=topic_id).order_by(func.random()).first()

    # Parse the solutions string into a list
    solutions = problem.solutions.split(',')
    shuffle(solutions)

    # Render the problem page template with the problem and solutions data
    return render_template('problem.html', problem=problem.unfold(), solutions=solutions)

@app.route('/problem/<problem_id>/check', methods=['POST'])
@login_required
def check_answer(problem_id):
    problem = Problem.query.get(problem_id)
    user_answer = request.form['answer']
    user = User.query.filter_by(username=session.get("username")).one()
    try:
        score = Score.query.filter_by(topic_id=problem.topic_id, user_id=user.id).one()
    except NoResultFound:
        score = Score(topic_id=problem.topic_id, user_id=user.id)
        db.session.add(score)
    score.problems_seen += 1

    # The correct answer is always the first listed in the problem's solutions
    correct_answer = problem.unfold().solutions[0]

    if user_answer == correct_answer:
        flash('Correct answer!', category="success")
        score.correct_answers += 1
    else:
        flash('Wrong answer, try again!')
    db.session.merge(score)
    db.session.commit()

    return redirect(url_for('list_problems'))


@app.route('/my_progress')
def my_progress():
    # Retrieve all the topics and their corresponding scores for the current user
    topics = Topic.query.all()
    user = User.query.filter_by(username=session.get("username")).one()
    scores = Score.query.filter_by(user_id=user.id).all()
    scores_dict = {score.topic_id: score for score in scores}

    # Determine which topics are completed, accessible, and active
    completed_topics = set()
    accessible_topics = set()
    active_topics = set()
    inactive_topics = set()
    for topic in topics:
        # Determine if the topic is active
        if topic.id in scores_dict and scores_dict[topic.id].problems_seen > 0:
            score = scores_dict[topic.id]
            topic.fraction = score.correct_answers / max(score.problems_seen, 4)
            
            # Determine if the topic is completed
            if topic.fraction > 0.95:
                completed_topics.add(topic.id)
            else:
                active_topics.add(topic)
        else:
            inactive_topics.add(topic.unfold())
    
    for topic in inactive_topics:
        # Determine if the topic is accessible
        print("TOPIC", topic.title)
        print("PRE", topic.prerequisites)
        print()
        if not topic.prerequisites or set(topic.prerequisites).issubset(completed_topics):
            accessible_topics.add(topic)

    # Select five random accessible topics and five active topics with the highest score
    random_accessible_topics = random.sample(list(accessible_topics), min(len(accessible_topics), 5))
    sorted_active_topics = sorted(
        list(active_topics),
        key=lambda topic: topic.fraction,
        reverse=True,
    )
    top_active_topics = sorted_active_topics[:min(len(sorted_active_topics), 5)]
    print("inactive", inactive_topics)
    return render_template('my_progress.html', random_accessible_topics=random_accessible_topics, top_active_topics=top_active_topics)



@app.route('/hack/<action>', methods=['GET', 'POST'])
def hack(action):
    match action:
        case "import_users":
            mysite.models.import_users_from_csv("users.csv")
        case "import_problems":
            mysite.models.load_problems_from_json("static/problems.json")
        case "clear_nontopic":
            db.session.query(Problem).filter_by(topic_id="").delete()
            db.session.commit()
        case "clear_commas":
            topics = Topic.query.all()
            for topic in topics:
                if ',' in topic.prerequisites:
                    topic.prerequisites = str(";__;").join(topic.prerequisites.split(","))
                    db.session.merge(topic)
                    db.session.commit()
        case "fix_pre":
            topics = Topic.query.all()
            for topic in topics:
                if ',' in topic.prerequisites:
                    topic.prerequisites = str(";__;").join(topic.prerequisites.split(","))
                    db.session.merge(topic)
                    db.session.commit()
    return redirect('/')

@app.route('/hack/<action>', methods=['GET', 'POST'])
@app.route('/hack/<action>/<arg>', methods=['GET', 'POST'], defaults={"arg": None})
def hack(action, arg=None):
    if action == "import_users":
        mysite.models.import_users_from_csv("users.csv")
    elif action == "import_problems":
        mysite.models.load_problems_from_json("static/problems.json")
    elif action == "clear_nontopic":
        db.session.query(Problem).filter_by(topic_id="").delete()
        db.session.commit()
    elif action == "clear_commas":
        topics = Topic.query.all()
        for topic in topics:
            if ',' in topic.prerequisites:
                topic.prerequisites = str(";__;").join(topic.prerequisites.split(","))
                db.session.merge(topic)
                db.session.commit()
    elif action == "fix_pre":
        topics = Topic.query.all()
        for topic in topics:
            if ',' in topic.prerequisites:
                topic.prerequisites = str(";__;").join(topic.prerequisites.split(","))
                db.session.merge(topic)
                db.session.commit()
    elif action== "toggle_editor":
        user = db.session.execute(db.select(User).filter_by(username=arg)).scalar_one()
        user.is_editor = not user.is_editor
        db.session.merge(user)
        db.session.commit()
        flash(f'Editor toggled! Now is {user.is_editor}.', category="success")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
