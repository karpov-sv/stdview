update_get_params = function(id, params) {
    console.log(id);
    $(id).attr('src', function(i, src) {
        var url = new URL(src, window.location);

        for (name in params)
            url.searchParams.set(name, params[name]);

        return url.href;
    });
}
