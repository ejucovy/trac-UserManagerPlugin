$(document).ready(function(){
	$(".expander").click(function(){
		expandedElement = $('#'+this.getAttribute('for'))[0];
		if(!expandedElement)
			expandedElement = $(this).parents('tbody:first').find('div[@name='+this.getAttribute('for')+']')[0];		
		if(!expandedElement) return false;

		if($(this).is(".expander_open")){
			$(this).removeClass("expander_open");
			expandedElement.style.display='none';
		}else{
				$(this).addClass("expander_open");
				expandedElement.style.display='block';
			}
	});
});
