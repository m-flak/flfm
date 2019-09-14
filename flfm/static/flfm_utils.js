function make_url(url_base, root, uri) {
    if (root.endsWith('/') && uri.startsWith('/')) {
        var new_uri = uri.replace(/^\//,' ').trim()
        if (url_base != null) {
            return `${url_base}${root}${new_uri}`;
        }
        else {
            return `${root}${new_uri}`;
        }
    }
    if (!url_base) {
        return `${root}${uri}`;
    }
    return `${url_base}${root}${uri}`;
}

function serve_params(serve_url, the_file) {
    return `${serve_url}?f=${the_file}&dl=1`;
}
