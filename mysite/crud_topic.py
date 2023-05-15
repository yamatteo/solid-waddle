from uuid import uuid4

from flask import flash, redirect, render_template, request, session, url_for

from mysite.authentication import editor_required, login_required
from mysite.init import app
from mysite.models import (NoResultFound, Problem, Score, Topic, TopicForm,
                           User, db)


@app.route('/topics')
@login_required
def list_topics():
    topics = Topic.query.all()
    user = User.query.filter_by(username=session.get("username")).one()
    for topic in topics:
        topic.num_problems = Problem.query.filter_by(topic_id=topic.id).count()
        try:
            score = Score.query.filter_by(topic_id=topic.id, user_id=user.id).one()
        except NoResultFound:
            score = Score(topic_id=topic.id, user_id=user.id)
            db.session.add(score)
        topic.score = int(100 * (score.correct_answers) / max(score.problems_seen, 4))
    
    db.session.commit()
    return render_template('list_topics.html', topics=topics)

@app.route('/topics/new', methods=['POST'])
@editor_required
def new_topic():
    topic = Topic(
        id=uuid4().hex,
        title="",
        description="",
        prerequisites="",
    )

    try:
        db.session.add(topic)
        db.session.commit()

        flash('New topic created', category="success")
        next_url = url_for('edit_topic', topic_id=topic.id)

    except Exception as err:
        print(err)
        flash("Error creating topic", category="danger")
        next_url = request.form.get('next_url') or url_for('list_topics')
    return redirect(next_url)



@app.route('/topics/edit/<topic_id>', methods=['GET', 'POST'])
@editor_required
def edit_topic(topic_id):
    topic = Topic.query.get(topic_id)
    all_topics = Topic.query.filter(Topic.id != topic_id).all()
    if ',' in topic.prerequisites:
        flash("Comma in prerequisites", category="warning")
    prerequisites = topic.prerequisites.split(';__;')
    if not topic:
        flash('Topic not found.', 'error')
        return redirect(url_for('list_topics'))

    form = TopicForm(obj=topic)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        topic.title = title
        topic.description = description
        
        db.session.merge(topic)
        db.session.commit()

    topic = Topic.query.get(topic_id)
    problems = Problem.query.filter_by(topic_id=topic.id).all()
    available_prerequisites = Topic.query.filter(~Topic.id.in_([topic.id, *prerequisites])).all()
    prerequisites = Topic.query.filter(Topic.id.in_(prerequisites)).all()
    return render_template(
        'edit_topic.html',
        form=form,
        topic=topic,
        topics=all_topics,
        available_prerequisites=available_prerequisites,
        prerequisites=prerequisites,
        problems=problems,
    )

@app.route('/topics/add_prerequisite', methods=['POST'])
@editor_required
def add_prerequisite():
    topic_id = request.form.get('topic_id')
    prerequisite = request.form.get('prerequisite')
    topic = Topic.query.get(topic_id)
    prerequisites = topic.prerequisites.split(';__;')
    prerequisites.append(prerequisite)
    topic.prerequisites = str(";__;").join([ topic for topic in set(prerequisites) if len(topic) > 0 ])
    
    print("TOPIC", topic.prerequisites)

    db.session.merge(topic)
    db.session.commit()

    next_url = request.form.get('next_url') or url_for('edit_topic', topic_id=topic.id)
    return redirect(next_url)

@app.route('/topics/remove_prerequisite', methods=['POST'])
@editor_required
def remove_prerequisite():
    topic_id = request.form.get('topic_id')
    prerequisite = request.form.get('prerequisite')
    topic = Topic.query.get(topic_id)
    prerequisites = topic.prerequisites.split(';__;')
    topic.prerequisites = str(";__;").join([ pre for pre in set(prerequisites) if pre != prerequisite ])
    
    db.session.merge(topic)
    db.session.commit()

    next_url = request.form.get('next_url') or url_for('edit_topic', topic_id=topic.id)
    return redirect(next_url)

@app.route("/topics/delete", methods=['POST'], defaults={"topic_id": None})
@app.route("/topics/delete/<topic_id>", methods=['POST'])
@editor_required
def delete_topic(topic_id):
    if topic_id is None:
        topic_id = request.form.get('topic_id')
    topic = Topic.query.get(topic_id)
    print(request.form)
    
    db.session.query(Topic).filter(Topic.id == topic_id).delete()
    db.session.commit()

    next_url = request.form.get('next_url') or url_for('list_topics')
    return redirect(next_url)