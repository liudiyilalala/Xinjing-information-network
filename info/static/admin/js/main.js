
    // 登出功能
    function log_out() {
        $.get('/admin/logout', function (resp){
            location.reload()
        })
    }