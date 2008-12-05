jQuery(document).ready(function($){
	$(".um_profile_macro .expander").click(function(){
		$(this).toggleClass('expander_open').parents('tr:first').next().find('.um_profile:first').toggle();
    })		
});
