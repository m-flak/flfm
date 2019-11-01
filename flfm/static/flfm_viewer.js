(function ($, _viewer_type, _viewer_srv_cache, _flfm_root, _viewer_current_file, _current_dir, _serve_url, _image_url) {
    resize_location_bar("#location-bar", "#commands");

    let media_list = new Promise(function(resolve, reject) {
        if (sessionStorage.getItem('MediaList')) {
            var the_data = JSON.parse(sessionStorage.getItem('MediaList'));
            var check_me = the_data.filter(e => e.cur === _viewer_current_file || e.prev === _viewer_current_file || e.next === _viewer_current_file);
            if (check_me.length >= 1) {
                resolve(the_data);
            } else {
                sessionStorage.removeItem('MediaList');
            }
        }
        if (!sessionStorage.getItem('MediaList')) {
            let wl = window.location;
            $.ajax({
                method: 'POST',
                url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/medialist'),
                data: { directory: _current_dir, whatkind: viewer_type }
            }).done(function(d) {
                sessionStorage.setItem('MediaList', JSON.stringify(d));
                resolve(d);
            });
        }
    });

    var slideshow_playing = false;
    var slideshow_timeout;

    function next_image() {
        if (slideshow_playing) {
            media_list.then(function(the_list) {
                var current = the_list.filter(e => e.cur === _viewer_current_file);
                if (current[0].next == null) {
                    _viewer_current_file = the_list[0].cur;
                } else {
                    _viewer_current_file = current[0].next;
                }
                let wl = window.location;
                var new_url = serve_params(make_url(`${wl.protocol}//${wl.host}`, _flfm_root, _serve_url), _viewer_current_file);
                $("img.viewer-image").cacheImages({url: new_url});
                $(document).trigger("slideshowEvent");
            });
        }
    }

    return (function(t, c) {
        if (t === 'text') {
            if (c) {
                return;
            }
            var file = get_url_vars()['f'];
            let wl = window.location;
            var big_file_url = serve_params(make_url(`${wl.protocol}//${wl.host}`, _flfm_root, _serve_url), file);
            $.ajax({
                method: 'GET',
                url: big_file_url,
                dataType: 'text',
            }).done(function(d) {
                $("#viewer-contents").text(d);
            });
        }
        else if (t === 'image') {
            if (!c) {
                var img_url = _image_url;
                img_url = img_url.trim();
                img_url = img_url.replace(/&\w+;/, '&');
                let wl = window.location;
                var full_url = make_url(`${wl.protocol}//${wl.host}`, _flfm_root, img_url);
                $("img.viewer-image").cacheImages({url: full_url});
            }

            $(document).on("slideshowEvent", function() {
                var slideshow_delay = localStorage.getItem('slideshowDelay') || 5000;
                slideshow_delay = Number(slideshow_delay);
                slideshow_playing = true;
                slideshow_timeout = window.setTimeout(next_image, slideshow_delay);
            });
            $("a#previous-file").on("click", function() {
                media_list.then(function(the_list) {
                    var current = the_list.filter(e => e.cur === _viewer_current_file);
                    if (current[0].prev != null) {
                        _viewer_current_file = current[0].prev;
                        let wl = window.location;
                        var new_url = serve_params(make_url(`${wl.protocol}//${wl.host}`, _flfm_root, _serve_url), _viewer_current_file);
                        $("img.viewer-image").cacheImages({url: new_url});
                    }
                });
            });
            $("a#next-file").on("click", function() {
                media_list.then(function(the_list) {
                    var current = the_list.filter(e => e.cur === _viewer_current_file);
                    if (current[0].next != null) {
                        _viewer_current_file = current[0].next;
                        let wl = window.location;
                        var new_url = serve_params(make_url(`${wl.protocol}//${wl.host}`, _flfm_root, _serve_url), _viewer_current_file);
                        $("img.viewer-image").cacheImages({url: new_url});
                    }
                });
            });
            $("a#play-files").on("click", function(e) {
                const classes = 'hidden invisible';
                let this_button = $(e.currentTarget);

                this_button.toggleClass(classes);
                $("a#stop-files").toggleClass(classes);
                $(document).trigger("slideshowEvent");
            });
            $("a#stop-files").on("click", function(e) {
                const classes = 'hidden invisible';
                let this_button = $(e.currentTarget);

                this_button.toggleClass(classes);
                $("a#play-files").toggleClass(classes);
                slideshow_playing = false;
                if (typeof slideshow_timeout !== 'undefined') {
                    if (slideshow_timeout != -1) {
                        window.clearTimeout(slideshow_timeout);
                        slideshow_timeout = -1;
                    }
                }
            });
        } else if (t === 'video') {
            /* abort if video.js not loaded */
            if (typeof videojs !== 'function') {
                return;
            }

            var video_filename;
            var socket = io();
            let vid = videojs('viewer-video');
            vid.responsive(true);
            let video_info = new Promise(function(resolve, reject) {
                var vi = {};
                let wl = window.location;
                $.ajax({
                    method: 'POST',
                    url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/mediainfo'),
                    data: { directory: _current_dir, file: _viewer_current_file }
                }).done(function(d) {
                    vi = d;
                    resolve(vi);
                }).fail(() => reject(vi));
            });

            socket.on("connect", function() {
                video_info.then(function(info) {
                    vid.width = info.width;
                    $("video").attr('width', info.width);
                    $(".video-holder").css('min-width', info.width);
                    vid.height = info.height;
                    $("video").attr('height', info.height);
                    $(".video-holder").css('min-height', info.width);
                    video_filename = info.filename;
                    socket.emit('prepare video', {
                        data: {
                            filename: video_filename,
                            shell_location: _viewer_current_file
                        }
                    });
                });
            });
            socket.on("video ready", function(d) {
                var source_string = JSON.parse(d).video_url;
                vid.src(source_string.concat('?start=0'));
                socket.emit('received_video');
                socket.close();
            });

            $("a#previous-file").on("click", function() {
                media_list.then(function(the_list) {
                    var current = the_list.filter(e => e.cur === _viewer_current_file);
                    if (current[0].prev != null) {
                        _viewer_current_file = current[0].prev;
                        video_info.then(function(info) {
                            var f = _viewer_current_file;
                            var mt = info.mimetype;
                            let wl = window.location;
                            var redir_to = viewer_params(`${wl.protocol}//${wl.host}${wl.pathname}`, f, mt);
                            document.location.assign(redir_to);
                        });
                    }
                });
            });

            $("a#next-file").on("click", function() {
                media_list.then(function(the_list) {
                    var current = the_list.filter(e => e.cur === _viewer_current_file);
                    if (current[0].next != null) {
                        _viewer_current_file = current[0].next;
                        video_info.then(function(info) {
                            var f = _viewer_current_file;
                            var mt = info.mimetype;
                            let wl = window.location;
                            var redir_to = viewer_params(`${wl.protocol}//${wl.host}${wl.pathname}`, f, mt);
                            document.location.assign(redir_to);
                        });
                    }
                });
            });
        }
    })(_viewer_type, _viewer_srv_cache);
}(jQuery, viewer_type, viewer_srv_cache, flfm_root, viewer_current_file, current_dir, serve_url, image_url));
