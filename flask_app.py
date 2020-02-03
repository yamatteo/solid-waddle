from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template("landing.html", mountain_ip=getattr(app, "mountain_ip", None))


@app.route("/set_mountain", methods=["POST"])
def set_mountain():
    from json import loads
    setattr(app, "mountain_ip", loads(request.data)["mountain_ip"])
    return "Ok"
