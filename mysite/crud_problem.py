from uuid import uuid4

from flask import flash, redirect, render_template, request, url_for

from mysite.authentication import editor_required, login_required
from mysite.init import app
from mysite.models import Problem, ProblemForm, Topic, db

@app.route('/problems')
@login_required
def list_problems():
    problems = Problem.query.all()
    topics = Topic.query.all()
    topics_dict = { topic.id: topic for topic in topics }
    for problem in problems:
        topic = topics_dict.get(problem.topic_id, None)
        problem.topic_title = topic.title if topic else "N/A"
    return render_template('list_problems.html', problems=problems, topics=topics)

@app.route('/problems/new', methods=['POST'], defaults={"topic_id": None})
@app.route('/problems/new/<topic_id>', methods=['POST'])
@editor_required
def new_problem(topic_id):
    """
    View function for creating a new problem.

    Args:
        topic_id (str): The ID of the topic that the problem belongs to.

    Returns:
        If the problem is successfully created, redirects the user to the edit_problem page for the new problem.
        Otherwise, redirects the user to the edit_topic page for the topic that the new problem was supposed to belong to.

    """
    if topic_id is None:
        topic_id = request.form.get("topic_id")

    # Create a new Problem object with a new ID for the problem using the uuid4 function.
    problem = Problem(
        id=uuid4().hex,
        topic_id=topic_id,
        text="",
        solutions=""
    )

    try:
        # Add the new problem to the database session and commit the changes.
        db.session.add(problem)
        db.session.commit()

        # If the new problem is successfully created, flash a success message and redirect to the edit_problem page.
        flash('New problem created', category="success")
        return redirect(url_for('edit_problem', problem_id=problem.id))

    except Exception as err:
        # If there was an error creating the new problem, log the error, flash a danger message, and redirect to the edit_topic page.
        print(err)
        flash("Error creating problem", category="danger")
        return redirect(url_for('edit_topic', topic_id=topic_id))


@app.route('/problems/edit/<problem_id>', methods=['GET', 'POST'])
def edit_problem(problem_id):
    problem = Problem.query.get(problem_id)
    topic = Topic.query.get(problem.topic_id)
    other_topics = Topic.query.filter(Topic.id != problem.topic_id)

    if request.method == 'GET':
        form = ProblemForm(obj=problem)
    elif request.method == 'POST':
        data = request.form.to_dict()
        data["solutions"] = [value for key, value in sorted(
            data.items()) if key[:8] == "solution"]
        data["solutions"] = str(";__;").join(data["solutions"])
        data["topic_id"] = problem.topic_id
        form = ProblemForm(data=data)
        if form.validate_on_submit():
            form.populate_obj(problem)
            db.session.commit()
            flash('Problem updated', category="success")
        else:
            flash("Error updating/displaying the problem", category="danger")

    return render_template('edit_problem.html', problem=problem.unfold(), topic=topic, topics=other_topics, form=form)


@app.route("/problems/move", methods=['POST'], defaults={"problem_id": None, "topic_id": None})
@app.route("/problems/move/<problem_id>/to/<topic_id>", methods=['POST'])
@editor_required
def move_problem(problem_id, topic_id):
    print(request.form)
    if problem_id is None:
        problem_id = request.form.get('problem_id')
    if topic_id is None:
        topic_id = request.form.get('topic_id')

    problem = Problem.query.get(problem_id)
    old_topic = problem.topic_id

    problem.topic_id = topic_id
    db.session.merge(problem)
    db.session.commit()

    next_url = request.form.get('next_url') or url_for('edit_topic', topic_id=old_topic)
    return redirect(next_url)


@app.route("/problems/delete", methods=['POST'], defaults={"problem_id": None})
@app.route("/problems/delete/<problem_id>", methods=['POST'])
@editor_required
def delete_problem(problem_id):
    if problem_id is None:
        problem_id = request.form.get('problem_id')
    problem = Problem.query.get(problem_id)
    print(request.form)
    
    db.session.query(Problem).filter(Problem.id == problem_id).delete()
    db.session.commit()

    next_url = request.form.get('next_url') or url_for('edit_topic', topic_id=problem.topic_id)
    return redirect(next_url)
