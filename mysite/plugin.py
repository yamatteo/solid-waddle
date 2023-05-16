
import os

from flask import Response
from mysite.init import app


@app.route('/plugin/structure', methods=['GET'])
def list_files(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return Response('\n'.join(file_list), mimetype='text/plain')
