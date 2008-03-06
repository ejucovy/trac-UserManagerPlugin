jQuery(document).ready(function($){
	$('div#um_active_users TABLE TFOOT FIELDSET LEGEND').click(function(){
		if($(this).is(".expander_open")){
			$(this).removeClass("expander_open");
			$(this.parentNode).addClass("close");}
		else {
			$(this).addClass("expander_open");
			$(this.parentNode).removeClass("close");}
		$( $(this.parentNode).find('.field-wrapper')[0]).toggle();
	});
});