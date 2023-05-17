"""Initializes the Flask application and sets up configurations and environment variables."""
import os
import random

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # load environment variables from .env file

app = Flask( __name__, template_folder=os.environ.get("TEMPLATE_FOLDER"))
app.secret_key = os.environ.get("SECRET_KEY")

@app.template_filter('shuffle')
def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq
