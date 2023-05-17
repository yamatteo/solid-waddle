
import ast
import os
from pathlib import Path

from flask import Response, render_template, request

from mysite.init import app

@app.route('/plugin/structure', methods=['GET', 'POST'])
def plugin_structure():
    base = Path(__file__).parent.parent
    whitelist_dirs = ["mysite", "static", "templates"]
    whitelist_ext = [".py", ".html"]

    file_list = []
    for root, dirs, files in os.walk(base):
        for file in files:
            path = (Path(root) / file).relative_to(base)
            if path.parts[0] in whitelist_dirs and path.suffix in whitelist_ext:
                file_list.append(path)

    if request.method == 'POST':
        selected_abstract_files = request.form.getlist('abstract-files')
        selected_fulltext_files = request.form.getlist('fulltext-files')

        abstract_files = []
        for file in selected_abstract_files:
            if file.endswith('.py'):
                abstract = get_pythonfile_abstract(base / file)
            elif file.endswith('.html'):
                abstract = get_html_template_abstract(base / file)
            else:
                abstract = None

            abstract_files.append({'name': file, 'abstract': abstract})

        fulltext_files = []
        for file in selected_fulltext_files:
            with open(base / file, 'r') as f:
                lines = f.readlines()
                fulltext_files.append({'name': file, 'lines': lines})

        return render_template('plugin_structure.html', file_list=file_list, abstract_files=abstract_files, fulltext_files=fulltext_files)

    return render_template('plugin_structure.html', file_list=file_list)


def get_pythonfile_abstract(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
        docstring = ast.get_docstring(tree)
        if docstring:
            return docstring.strip()
    return None

def get_html_template_abstract(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        abstract = ''
        comment_block_started = False

        for line in lines:
            line = line.strip()

            if line.startswith('<!--') and not comment_block_started:
                comment_block_started = True
                continue

            if comment_block_started and line.endswith('-->'):
                comment_block_started = False
                break

            if comment_block_started:
                abstract += line + ' '

        abstract = abstract.strip()
        return abstract if abstract else None
