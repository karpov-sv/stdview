update_get_params = function(id, params) {
    /* Show 'loading' overlay */
    $(id).parent().addClass('stdview-image-loading');

    $(id).one('load', function() {
        /* Hide 'loading' overlay */
        $(id).parent().removeClass('stdview-image-loading');
    }).attr('src', function(i, src) {
        var url = new URL(src, window.location);

        for (name in params)
            url.searchParams.set(name, params[name]);

        return url.href;
    });
}
