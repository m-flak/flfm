function make_url(url_base, root, uri) {
    var the_root = root;
    if (root.length > 1 || root !== '/') {
        if (uri.startsWith(root)) {
            the_root = '/';
        }
    }
    if (the_root.endsWith('/') && uri.startsWith('/')) {
        var new_uri = uri.replace(/^\//,' ').trim()
        if (url_base != null) {
            return `${url_base}${the_root}${new_uri}`;
        }
        else {
            return `${the_root}${new_uri}`;
        }
    }
    if (!url_base) {
        return `${the_root}${uri}`;
    }
    return `${url_base}${the_root}${uri}`;
}

function serve_params(serve_url, the_file) {
    return `${serve_url}?f=${the_file}&dl=1`;
}

function get_url_vars() {
    var vars = {};
    try {
        var url = window.parent.parent.location.href;
        var parts = url.split("#")[0].replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
            vars[key] = value;
        });
    } catch (e) {
        // do nothing
    }
    return vars;
}

function resize_location_bar(selector, buttons_selector, max_size=18) {
    let the_location = $(selector).children("h4");
    var strlen = the_location.data('strlen');
    var buttwidth = $(buttons_selector).width();
    var vw, fs;

    if (typeof window.parent.parent.screen.availWidth === 'undefined') {
        vw = window.parent.parent.screen.width;
    } else {
        vw = window.parent.parent.screen.availWidth;
    }

    fs = Math.round(vw/strlen);
    fs -= Math.round(fs*buttwidth/vw);

    if (fs > max_size) {
        return;
    } else if (fs < 12 && fs >= 10) {
        the_location.css('line-height', '1.5');
    } else if (fs < 10) {
        the_location.css('line-height', '2');
    }

    the_location.css('font-size', `${fs}pt`);
}
