(function ($, _dashboard_tab) {
    /* Capitalize the Tab Names */
    $(".dash-tab > a").each(function() {
        var tab_text = $(this).text().trim();
        var first_letter = tab_text.slice(0, 1).toUpperCase();
        var the_rest_of = tab_text.slice(-1*tab_text.length+1);
        $(this).text(first_letter+the_rest_of);
    });

    /* Dashboard tab-specific stuff */
    if (_dashboard_tab === 'admin') {
        /* Resize the damn form */
        const font_size = 14;

        var labels = $("form").find("li > label").length;
        labels += $("form").find("th > label").length;

        var form_height = labels * font_size;
        form_height *= 2;
        $("form").css('height', form_height);

        /* Fix the damn captions */
        var new_labels = new Array();
        $("tr").find("input[type=hidden]").each(function() {
            new_labels.push($(this).attr('value'));
        });
        $("li > label").each(function(i) {
            try {
                $(this).text(new_labels[i]);
            }
            catch (e) {
                /* do nuthin' */
            }
        });
    }
}(jQuery, dashboard_tab));
