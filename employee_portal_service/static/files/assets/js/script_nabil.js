"use strict";
$(document).ready(function() {
    var direction_str = $('#direction_str').val();
    if (direction_str=='rtl'){
        $( ".js_change_lang" ).each(function( index ) {
            if(($(this).data( "url_code" )=='ar_SY')||($( this ).data( "url_code" )=='ar')){
                $('#span_change_lang').html($( this ).data( "url_name" ));
            }
        });
    }else{
        $( ".js_change_lang" ).each(function( index ) {
            if($(this).data( "url_code" )=='en'){
                $('#span_change_lang').html($( this ).data( "url_name" ));
            }
        });
    }
});