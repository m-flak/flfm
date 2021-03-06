import os
import werkzeug.urls as wurls

# quickly make a url w/ args using werkzeug
def make_arg_url(base_url, arg_dict):
    with_args = wurls.Href(base_url)
    return with_args(arg_dict)

# Get the user-config'd or default banner value from a Flask app instance
def get_banner_string(app):
    banner = app.config['BANNER']
    banner_type = app.config['BANNER_TYPE']
    banner_val = banner

    if banner_type not in ('string', 'file'):
        raise ValueError

    if banner_type == 'file':
        try:
            with open(banner, 'r') as bff:
                value = bff.readline()
                banner_val = value.strip()
        except (FileNotFoundError, PermissionError):
            banner_val = 'Flask File Manager'

    return banner_val

# generate a nice, big random integer
def make_filepond_id():
    return ord(os.urandom(1))<<16|ord(os.urandom(1))<<8|ord(os.urandom(1))<<4|ord(os.urandom(1))
