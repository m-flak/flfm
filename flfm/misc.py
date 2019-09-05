
def get_banner_string(app):
    banner = app.config['BANNER']
    banner_type = app.config['BANNER_TYPE']
    banner_val = banner

    if banner_type != 'string' and banner_type != 'file':
        raise ValueError

    if banner_type == 'file':
        try:
            with open(banner, 'r') as bff:
                value = bff.readline()
                banner_val = value.strip()
        except (FileNotFoundError, PermissionError):
            banner_val = 'Flask File Manager'

    return banner_val
