import os
from flask import (
    Blueprint, render_template, g, request
)
from flfm.shell.rules import enforce_mapped, needs_rules, MappedDirectories
from .vcache import vcache

viewer = Blueprint('viewer', __name__, template_folder='templates')

@viewer.route('/view')
@needs_rules
def view_file():
    mapped_dirs = MappedDirectories.from_rules(g.fm_rules)
    input_file = request.args['f']
    current_dir = os.path.dirname(input_file)
    enforce_mapped(mapped_dirs, current_dir)

    file_to_view = vcache.view_file(input_file)

    return render_template('viewer.html', current_file=input_file,
                           current_dir=current_dir,
                           current_contents=file_to_view)