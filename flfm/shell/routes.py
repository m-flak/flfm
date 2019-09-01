import os
import re
import mimetypes
import filetype
from flask import (
    Blueprint, render_template, g, request, send_file, session, abort, redirect,
    url_for, current_app
)
from .paths import ShellPath
from .rules import enforce_mapped, needs_rules, MappedDirectories
from .uploads import UploadedFile

shell = Blueprint('shell', __name__, template_folder='templates')

def make_filepond_id():
    return ord(os.urandom(1))<<16|ord(os.urandom(1))<<8|ord(os.urandom(1))<<4|ord(os.urandom(1))

# Set cache-control header to no-store so the viewer will always work if enabled
@shell.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    else:
        response.headers['Cache-Control'] = 'no-store'
    return response

@shell.before_request
def make_vars_available():
    g.available_vars = {
        'app_root': current_app.config.get('APPLICATION_ROOT', '/')
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
    mapped_dirs = MappedDirectories.from_rules(g.fm_rules)
    enforce_mapped(mapped_dirs, view_path_fixed)

    shell_path = ShellPath(view_path_fixed, mapped_dirs)
    return render_template('shell.html', whereami=shell_path.str_path,
                           folder_contents=shell_path.children,
                           cwd_mapping=shell_path.mapping)

@shell.route('/serve')
@needs_rules
def serve_file():
    mapped_dirs = MappedDirectories.from_rules(g.fm_rules)
    input_file = request.args['f']
    enforce_mapped(mapped_dirs, os.path.dirname(input_file))

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
        and re.match('text/', mimetype) is not None:
            return redirect("{}?f={}".format(url_for('viewer.view_file'),
                                            input_file))

    return send_file(input_file, mimetype=mimetype, as_attachment=True,
                     attachment_filename=os.path.basename(input_file))

@shell.route('/process', methods=['POST'])
@needs_rules
def process():
    mapped_dirs = MappedDirectories.from_rules(g.fm_rules)
    content_type = re.search(r"^.+;",
                             request.headers['Content-Type']).group(0).strip(';')

    if content_type == 'multipart/form-data':
        filename = request.files['filepond'].filename
        upload_path = request.headers['X-Uploadto']
        filepond_id = make_filepond_id()
        enforce_mapped(mapped_dirs, upload_path, True)

        s_entry = 'tmp_{}'.format(filepond_id)
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
