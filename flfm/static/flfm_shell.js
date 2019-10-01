(function ($, _flfm_root, _uploads_allowed, _upload_where) {
    /* Code unrelated to uploads goes here */
    /* All functionality should go in here */
    function shell_user_interface($, _flfm_root, _uploads_allowed, _upload_where) {
        $("a#buttonUp").on("click", function() {
            var new_url = window.location.href.replace(/(?!\/shell)\/\w+(?:[%1-9]*\w*)*#?$/, '');
            document.location.assign(new_url);
        });

        $("#settingsModal").on("show.bs.modal", function(e) {
            var cookie = Cookies.get('flfm_viewer');
            if (cookie != null) {
                let vform = $(e.currentTarget).find("form#settingsModalForm-1").get(0);
                for (var i = 0; i < vform.elements.length; i++) {
                    if (vform.elements[i].value === cookie) {
                        vform.elements[i].checked = true;
                    }
                }
            }
            var slideshow_delay = localStorage.getItem('slideshowDelay') || 5000;
            slideshow_delay = Number(slideshow_delay);
            $(e.currentTarget).find("form#settingsModalForm-2").children().each(function(i,e) {
                if (e.id === 'slideshowDelay') {
                    $(this).val(slideshow_delay);
                }
            });
        });

        $("#settingsModalApplyButton").on("click", function() {
            let vform = $("#settingsModal").find("form#settingsModalForm-1").get(0);
            var viewer_new_val = null;
            for (var i = 0; i < vform.elements.length; i++) {
                if (vform.elements[i].checked == true) {
                    viewer_new_val = vform.elements[i].value;
                }
            }
            if (!viewer_new_val) {
                return;
            }
            if (Cookies.get('flfm_viewer') != null) {
                Cookies.remove('flfm_viewer');
            }
            Cookies.set('flfm_viewer', viewer_new_val);

            $("#settingsModal").find("form#settingsModalForm-2").children().each(function(i,e) {
                if (e.id === 'slideshowDelay') {
                    var value = $(this).val();
                    localStorage.setItem('slideshowDelay', value);
                }
            });
        });

        resize_location_bar("#location-bar", "#commands");
    }
    /* creates bootstrap alerts. used in the uploader */
    function make_error_alert(error_string) {
        $("#uploadModalAlerts").append(`<div class='alert alert-danger' role='alert'>${error_string}</div>`);
    }

    /**** BEGIN CODE ****/

    if (!_uploads_allowed) {
        $("a#buttonUpload").addClass('disabled');
        return shell_user_interface($, _flfm_root, _uploads_allowed, _upload_where);
    }

    var fp_object = null;
    var ul_finished = false;

    $("#uploadModal").on("show.bs.modal", function(e) {
        let file_input = $(e.currentTarget).find("input[type='file']").get(0);
        $(e.currentTarget).find("button#uploadModalFinishButton").attr('disabled', true);
        if (!fp_object) {
            fp_object = FilePond.create(file_input);
        }
        let wl = window.location;
        fp_object.setOptions({
            allowPaste: false,
            allowReplace: false,
            allowRevert: false,
            server: {
                url: `${wl.protocol}//${wl.host}`,
                process: {
                    url: make_url(null, _flfm_root, '/process'),
                    method: 'POST',
                    headers: {
                        'X-Uploadto': _upload_where
                    },
                },
            },
            onprocessfile: function(err,file) {
                if (!err) {
                    var serverid = file.serverId;
                    var ul_dir = _upload_where;
                    $.ajax({
                        method: 'POST',
                        url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/process'),
                        data: { id: serverid },
                        dataType: 'text'
                    }).done(function(d) {
                        if (d === 'SUCCESS') {
                            let bt_fin = $("#uploadModal").find("button#uploadModalFinishButton");
                            bt_fin.attr('disabled', false);
                        } else if (d === 'EXISTS') {
                            make_error_alert("File already exists on server!");
                        } else if (d === 'NOUPLOAD') {
                            make_error_alert("File failed to be uploaded!");
                        }
                    });
                }
            },
        });
    });

    $("#uploadModal").find("div.modal-footer").children("button").on("click", function(e) {
        var tc = e.currentTarget.textContent.trim();
        if (tc === 'Finish') {
            ul_finished = true;
        }
    });

    $("#uploadModal").on("hidden.bs.modal", function (e) {
        let file_input = $(e.currentTarget).find("input[type='file']").get(0);
        $(e.currentTarget).find("button#uploadModalFinishButton").attr('disabled', false);
        if (fp_object) {
            fp_object.destroy(file_input);
            delete fp_object;
            fp_object = null;
        }
        let alerts = $("#uploadModalAlerts").children();
        if (alerts.length > 0) {
            alerts.each(function() {
                $(this).remove();
            });
        }
        if (ul_finished) {
            ul_finished = false;
            if (sessionStorage.getItem('MediaList')) {
                sessionStorage.removeItem('MediaList');
            }
            window.location.reload(true);
        }
    });

    return shell_user_interface($, _flfm_root, _uploads_allowed, _upload_where);
}(jQuery, flfm_root, uploads_allowed, upload_where));
