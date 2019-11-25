(function ($, _flfm_root, _uploads_allowed, _upload_where) {
    /* Code unrelated to uploads goes here */
    /* All functionality should go in here */
    function shell_user_interface($, _flfm_root, _uploads_allowed, _upload_where) {
        $("a#buttonUp").on("click", function() {
            var new_url = window.location.href.replace(/(?!\/shell)\/\w+(?:[%1-9]*\w*)*#?$/, '');
            document.location.assign(new_url);
        });
        $("a#buttonRoot").on("click", function() {
            let whl = window.location.href;
            const shellfrag = '/shell';
            var new_url = whl.slice(0, whl.indexOf(shellfrag)+shellfrag.length);
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

        $("#deleteConfirmModal").on("show.bs.modal", function(e) {
            let dcm_storage = $("#deleteConfirmModal").find("#deleteConfirmModal-Data");
            var dcm_var = document.createElement('input');
            var delete_what = e.relatedTarget.dataset['deletewhat'];

            /* store state within the modal's dom tree */
            dcm_var.type = 'hidden';
            dcm_var.name = 'dcm-var-dw';
            dcm_var.id = dcm_var.name;
            dcm_var.value = delete_what;
            dcm_storage.append($(dcm_var));

            var filename = delete_what.split('/').pop();
            $("#deleteConfirmModalLabel").text($("#deleteConfirmModalLabel").text()+` ${filename}`);
            $("#deleteConfirmModalMSG").text($("#deleteConfirmModalMSG").text()+` ${filename}?`);
        });

        $("#deleteConfirmModalDeleteButton").on("click", function() {
            let dcm_storage = $("#deleteConfirmModal").find("#deleteConfirmModal-Data");
            var delete_what = dcm_storage.find("#dcm-var-dw").val();

            let wl = window.location;
            $.ajax({
                method: 'POST',
                url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/perform'),
                data: { action: 'delete', p1: delete_what },
                dataType: 'text'
            }).done(function(d) {
                if (d === 'SUCCESS') {
                    window.location.reload(true);
                }
            });
        });

        $("#deleteConfirmModal").on("hidden.bs.modal", function(e) {
            let dcm_storage = $("#deleteConfirmModal").find("#deleteConfirmModal-Data");
            var filename = dcm_storage.find("#dcm-var-dw").val().split('/').pop();

            /* reset the modal's state */
            dcm_storage.empty();

            /* reset the labels of the modal */
            var modal_lbl = $("#deleteConfirmModalLabel").text();
            var modal_msg = $("#deleteConfirmModalMSG").text();
            modal_lbl = modal_lbl.slice(0, modal_lbl.indexOf(filename));
            modal_msg = modal_msg.slice(0, modal_msg.indexOf(filename));
            $("#deleteConfirmModalLabel").text(modal_lbl);
            $("#deleteConfirmModalMSG").text(modal_msg);
        });
        /***********************************************************/
        /******************* RENAME MODAL **************************/
        /***********************************************************/
        $("#renameModal").on("show.bs.modal", function(e) {
            let rnm_storage = $("#renameModal").find("#renameModal-Data");
            var rnm_var = document.createElement('input');
            var rename_what = e.relatedTarget.dataset['renamewhat'];

            /* store state within the modal's dom tree */
            rnm_var.type = 'hidden';
            rnm_var.name = 'rnm-var-rw';
            rnm_var.id = rnm_var.name;
            rnm_var.value = rename_what;
            rnm_storage.append($(rnm_var));

            var current_filename = rename_what.split('/').pop();
            $("#renameModalLabel").text($("#renameModalLabel").text()+` ${current_filename}`);
        });

        $("#renameModalRenameButton").on("click", function() {
            let rnm_storage = $("#renameModal").find("#renameModal-Data");
            let rnm_widgets = $("#renameModal").find("#renameModal-Widgets");
            var rename_what = rnm_storage.find("#rnm-var-rw").val();
            var the_new_name = rnm_widgets.find("#renameNewName").val();

            if (the_new_name.length >= 1) {
                let wl = window.location;
                $.ajax({
                    method: 'POST',
                    url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/perform'),
                    data: { action: 'rename', p1: rename_what, p2: the_new_name },
                    dataType: 'text'
                }).done(function(d) {
                    if (d === 'SUCCESS') {
                        window.location.reload(true);
                    }
                });
            }
        });

        $("#renameModal").on("hidden.bs.modal", function(e) {
            let rnm_storage = $("#renameModal").find("#renameModal-Data");
            let rnm_widgets = $("#renameModal").find("#renameModal-Widgets");
            var current_filename = rnm_storage.find("#rnm-var-rw").val().split('/').pop();

            /* reset the modal's state */
            rnm_storage.empty();

            /* reset the labels of the modal */
            var modal_lbl = $("#renameModalLabel").text();
            modal_lbl = modal_lbl.slice(0, modal_lbl.indexOf(current_filename));
            $("#renameModalLabel").text(modal_lbl);

            /* reset the textfield */
            rnm_widgets.find("#renameNewName").val('');
        });
        /***********************************************************/
        /******************* NEW DIR MODAL **************************/
        /***********************************************************/
        $("#newDirectoryModalNewButton").on("click", function() {
            let ndm_storage = $("#newDirectoryModal").find("#newDirectoryModal-Data");
            let ndm_widgets = $("#newDirectoryModal").find("#newDirectoryModal-Widgets");
            var where_to_create = ndm_storage.find("#newDirectoryWhere").val();
            var directory_name = ndm_widgets.find("#newDirectoryNewDir").val();

            if (directory_name.length >= 1) {
                let wl = window.location;
                $.ajax({
                    method: 'POST',
                    url: make_url(`${wl.protocol}//${wl.host}`, _flfm_root, '/newdir'),
                    data: { where: where_to_create, name: directory_name },
                    dataType: 'text'
                }).done(function(d) {
                    if (d === 'SUCCESS') {
                        window.location.reload(true);
                    }
                });
            }
        });

        $("#newDirectoryModal").on("hidden.bs.modal", function() {
            let ndm_widgets = $("#newDirectoryModal").find("#newDirectoryModal-Widgets");

            ndm_widgets.find("#newDirectoryNewDir").val('');
        });
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
