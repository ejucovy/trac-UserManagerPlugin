jQuery(document).ready(function($){
	$('div#um_active_users TABLE TFOOT FIELDSET LEGEND').click(function(){
		$(this).toggleClass('expander_open').parent().toggleClass('close').find('>.field-wrapper').toggle();
	});
});