import os
from flask import (
    Blueprint, render_template, g, request, current_app, abort, make_response
)
from flfm.shell.paths import ShellPath
from flfm.shell.rules import enforce_mapped, needs_rules, MappedDirectories
from flfm.misc import get_banner_string
from .vcache import vcache

viewer = Blueprint('viewer', __name__, template_folder='templates')

# These are globals for the Jinja2 engine
# pylint: disable=duplicate-code
@viewer.before_request
def make_vars_available():
    g.available_vars = {
        'app_root': current_app.config.get('APPLICATION_ROOT', '/'),
        'banner_string': get_banner_string(current_app),
        'registration_enabled': current_app.config.get('ACCOUNT_REGISTRATION_ENABLED',
                                                       False),
    }

@viewer.route('/view')
@needs_rules
def view_file():
    input_file = request.args['f']
    if_mimetype = request.args['mt']
    current_dir = os.path.dirname(input_file)
    mapped_dirs = MappedDirectories.from_shell_path(ShellPath(current_dir)).\
                  apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
    enforce_mapped(mapped_dirs, current_dir)

    # If the file is not cacheable (ie: too large), we'll send the path
    # instead in order to generate a serve_file link instead later on
    was_cacheable = vcache.is_file_cacheable(input_file)
    cache_id = -1
    if was_cacheable:
        file_to_view = vcache.view_file(input_file)
        cache_id = hash(file_to_view)
    else:
        file_to_view = input_file

    return render_template('viewer.html', was_cacheable=was_cacheable,
                           current_file=input_file, current_dir=current_dir,
                           current_contents=file_to_view, mimetype=if_mimetype,
                           cache_id=cache_id)

@viewer.route('/fetch/<int:cacheid>')
def fetch(cacheid):
    mimetype = request.args.get('mimetype', 'application/octet-stream')

    the_key = None
    # apparently, the key is the filename instead of its hash. whatever -_-
    for i, k in enumerate(vcache.cache):
        k_hash = hash(vcache.view_file(k[0]))
        if k_hash == cacheid:
            the_key = k[0]
            break

    if the_key is None:
        abort(404)

    cached_file = make_response(vcache.view_file(the_key).read_contents())
    cached_file.mimetype = mimetype
    return cached_file
