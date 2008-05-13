
jQuery(document).ready(function($){
    // Hide permissions 
	permissions = $('.um_permissions_group').not('.um_permissions_group_groups');
	permissions.hide();
	
	groups = jQuery('.um_permissions_group_groups')[0];  
	
	toggle_link = document.createElement('A');
    toggle_link.innerHTML="[ Show all permissions ]";
    toggle_link.href="#";
    $(toggle_link).css('margin-bottom','5px');
    
	groups.parentNode.insertBefore(toggle_link, permissions[0]);

    jQuery(toggle_link).click(function(){
		permissions.toggle(); 
		if($(permissions[0]).is(':visible'))
			toggle_link.innerHTML="[ Hide all permissions ]";
		else
		    toggle_link.innerHTML="[ Show all permissions ]";
		return false;
		});
});
