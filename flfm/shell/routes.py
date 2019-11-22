import os
import re
import json
import mimetypes
import shutil
import filetype
from flask import (
    Blueprint, render_template, g, request, send_file, session, abort, redirect,
    url_for, current_app, make_response
)
from flask_login import login_required
from flfm.misc import get_banner_string, make_arg_url, make_filepond_id
import flfm.shell.video as vid_fmt
from .paths import ShellPath, create_proper_shellitem
from .rules import enforce_mapped, needs_rules, MappedDirectories
from .uploads import UploadedFile

shell = Blueprint('shell', __name__, template_folder='templates')

def is_viewable_mimetype(mimetype):
    conditions = [re.match('text/', mimetype) is not None,
                  re.match('image/', mimetype) is not None,
                  re.match('video/', mimetype) is not None]

    for c in conditions:
        if c:
            return c

    return False

# Set cache-control header to no-store so the viewer will always work if enabled
@shell.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    else:
        response.headers['Cache-Control'] = 'no-store'
    return response

# These are globals for the Jinja2 engine
# pylint: disable=duplicate-code
@shell.before_request
def make_vars_available():
    g.available_vars = {
        'app_root': current_app.config.get('APPLICATION_ROOT', '/'),
        'banner_string': get_banner_string(current_app),
        'registration_enabled': current_app.config.get('ACCOUNT_REGISTRATION_ENABLED',
                                                       False),
    }

@shell.route('/shell')
@needs_rules
def shell_default():
    return render_template('default.html',
                           mapped_dirs=MappedDirectories.from_rules(g.fm_rules))

@shell.route('/shell/<path:view_path>')
@needs_rules
def shell_view(view_path):
    view_path_fixed = '/{}'.format(view_path)
    mapped_dirs = MappedDirectories.from_shell_path(ShellPath(view_path_fixed)).\
                  apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
    enforce_mapped(mapped_dirs, view_path_fixed)

    shell_path = ShellPath(view_path_fixed, mapped_dirs)
    return render_template('shell.html', whereami=shell_path.str_path,
                           folder_contents=shell_path.children,
                           cwd_mapping=shell_path.mapping)

@shell.route('/serve')
@needs_rules
def serve_file():
    input_file = request.args['f']
    input_dir = os.path.dirname(input_file)
    mapped_dirs = MappedDirectories.from_shell_path(ShellPath(input_dir)).\
                  apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
    enforce_mapped(mapped_dirs, input_dir)

    mimetype = mimetypes.guess_type(input_file)[0]
    if mimetype is None:
        try:
            mimetype = filetype.guess(input_file).mime
        except AttributeError:
            mimetype = 'application/octet-stream'

    force_download = request.args.get('dl', 0)
    # if the url contains dl=1 skip viewer check altogether
    if 'flfm_viewer' in request.cookies and force_download == 0:
        if request.cookies['flfm_viewer'] == 'enabled' \
        and is_viewable_mimetype(mimetype):
            return redirect(make_arg_url(url_for('viewer.view_file'),
                                         {'f': input_file, 'mt': mimetype,}))

    return send_file(input_file, mimetype=mimetype, as_attachment=True,
                     attachment_filename=os.path.basename(input_file))

@shell.route('/process', methods=['POST'])
@needs_rules
def process():
    content_type = re.search(r"^.+;",
                             request.headers['Content-Type']).group(0).strip(';')

    # Important to Logic
    # pylint: disable=no-else-return

    # See: https://pqina.nl/filepond/docs/patterns/api/server/
    if content_type == 'multipart/form-data':
        filename = request.files['filepond'].filename
        upload_path = request.headers['X-Uploadto']
        filepond_id = make_filepond_id()
        mapped_dirs = MappedDirectories.from_shell_path(ShellPath(upload_path)).\
                      apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
        enforce_mapped(mapped_dirs, upload_path, True)

        s_entry = 'tmp_{}'.format(filepond_id)
        # we want the filepond id number to persist between request contexts
        # hence, the use of flask_session `session` object
        session[s_entry] = (filepond_id, upload_path, filename)
        upload_file = UploadedFile(filepond_id, upload_path, filename)
        upload_file.create_temporary()
        # check if it already exists
        if upload_file.permanent:
            abort(400)
        request.files['filepond'].save(upload_file.file)

        return '{}'.format(filepond_id)
    elif content_type == 'application/x-www-form-urlencoded':
        s_entry = 'tmp_{}'.format(request.form['id'])
        filepond_id, upload_path, filename = session[s_entry]
        uploaded_file = UploadedFile(filepond_id, upload_path, filename)
        try:
            uploaded_file.make_permanent()
        except FileExistsError:
            return 'EXISTS'
        except FileNotFoundError:
            return 'NOUPLOAD'

        return 'SUCCESS'

    return ''

@shell.route('/medialist', methods=['POST'])
@needs_rules
def medialist():
    # generates a linked-list of matching files in a directory
    def gen_ml(dem_files):
        for i, shellfile in enumerate(dem_files):
            prev, cur, nxt = None, None, None
            cur = shellfile.path
            if i > 0:
                prev = dem_files[i-1].path
            if i+1 < len(dem_files):
                nxt = dem_files[i+1].path
            yield dict({
                'prev': prev,
                'cur': cur,
                'next': nxt,
            })
    #       #       #       #       #       #
    where_at = request.form.get('directory', None)
    what_kind = request.form.get('whatkind', None)

    if where_at is None or what_kind is None:
        abort(400)

    this_path = ShellPath(where_at)
    mapped_dirs = MappedDirectories.from_shell_path(this_path).\
                  apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
    enforce_mapped(mapped_dirs, where_at)

    matched_media = list(filter(lambda f: f.is_mimetype_family(what_kind),
                                this_path.files))

    # create the linked-list like object for the frontend
    the_medialist = list(gen_ml(matched_media))

    resp = make_response(json.dumps(the_medialist))
    resp.mimetype = 'application/json'
    return resp

@shell.route('/mediainfo', methods=['POST'])
@needs_rules
def mediainfo():
    media_info = dict()
    where_at = request.form.get('directory', None)
    what_file = request.form.get('file', None)

    if where_at is None or what_file is None:
        abort(400)

    this_path = ShellPath(where_at)
    mapped_dirs = MappedDirectories.from_shell_path(this_path).\
                  apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
    enforce_mapped(mapped_dirs, where_at)

    # Fix `what_file` if it redundantly includes the path
    if where_at in what_file:
        file_loc, file_name = os.path.split(what_file)
        if not file_name or file_name is None:
            abort(400)
        what_file = file_name

    # Abort if file can't be found.
    try:
        shell_file = list(filter(lambda f: f.name == what_file, this_path.files))[0]
    except IndexError:
        abort(400)

    media_info['filename'] = shell_file.name

    if 'mp4' in shell_file.mimetype:
        video = vid_fmt.MP4File(shell_file.path)
        media_info['width'] = video.video_width
        media_info['height'] = video.video_height
    else:
        abort(501)

    media_info['mimetype'] = shell_file.mimetype

    resp = make_response(json.dumps(media_info))
    resp.mimetype = 'application/json'
    return resp

@shell.route('/perform', methods=['POST'])
@needs_rules
@login_required
def perform():
    # get parameters, they exist as {'p1': blah, ...}
    def get_parameters(formdata):
        for k in formdata.keys():
            if re.match(r'p([0-9]*)', k):
                yield formdata[k]
    # do the rule enforcement
    # dir - ShellDirectory, file - ShellFile
    def do_enforcement(dir, file):
        input_dir = ''
        if dir is not None:
            input_dir = dir.path
        elif file is not None:
            input_dir = file.parent_directory()
        mapped_dirs = MappedDirectories.from_shell_path(ShellPath(input_dir)).\
                      apply_rule_map(MappedDirectories.from_rules(g.fm_rules))
        enforce_mapped(mapped_dirs, input_dir)
        return

    # # # # # # # # # # # # # # # # # # # # # # # # #

    action = request.form.get('action', None)
    parameters = tuple(get_parameters(request.form))
    # action name, number of parameters required
    action_params = dict(delete=1, rename=2)

    # validate requested action and parameters associated with it
    if action is None or not parameters:
        abort(400)
    if action not in action_params.keys():
        abort(400)
    if len(parameters) != action_params[action]:
        abort(400)

    if 'delete' in action:
        target = create_proper_shellitem(parameters[0])

        if target.file:
            do_enforcement(None, target)
            os.remove(target.path)
        else:
            do_enforcement(target, None)
            shutil.rmtree(target.path, True)
    elif 'rename' in action:
        target = create_proper_shellitem(parameters[0])
        new_name = '{}/{}'.format(target.parent_directory(), parameters[1])

        if target.file:
            do_enforcement(None, target)
            os.rename(target.path, new_name)
        else:
            do_enforcement(target, None)
            os.rename(target.path, new_name)

    return 'SUCCESS'
