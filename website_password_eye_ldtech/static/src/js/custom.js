
console.log("===========ODOO17===========")

$(document).ready(function(){

    $("#b2b_toggle_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#password").attr("type", type);
    });

    $("#b2b_toggle_confirm_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#confirm_password").attr("type", type);
    });

});


