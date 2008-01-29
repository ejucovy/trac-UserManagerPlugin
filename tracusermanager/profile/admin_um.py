# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from trac.util.translation import _
from trac.web.chrome import add_stylesheet

from tracusermanager.admin import IUserManagerPanelProvider, IUserListCellContributor
from tracusermanager.profile.api import UserProfileManager

class UserProfileUserManagerPanel(Component):
    
    implements(IUserManagerPanelProvider, IUserListCellContributor)
    
    # IUserManagerPanelProvider
    def get_usermanager_admin_panels(self, req):
        return [('profile', _('Profile'))]
    
    def render_usermanager_admin_panel(self, req, panel, user, path_info):
        data = dict(messages=[], errors=[],
                    um_profile_fields=UserProfileManager(self.env).get_user_profile_fields())
        
        if req.method=="POST":
            if req.args.has_key("um_profile_picture_remove"):
                if UserProfileManager(self.env).remove_user_file(user["picture_href"]):
                    del user["picture_href"]
                    if user.save():
                        data['messages'].append(_("Successfully removed %s's picture.")%(user.username))
            if req.args.has_key("um_profile_update"):
                for field in data['um_profile_fields'].keys():
                    if req.args.has_key("um_profile_%s"%(field)):
                        if data['um_profile_fields'][field]['type']=='file':
                            user_file_new = UserProfileManager(self.env).get_uploaded_file_href(req, user, field, "um_profile_%s"%(field))
                            user_file_old = user[field]
                            if user_file_new!=user_file_old:
                                user[field] = user_file_new
                                if user_file_old:
                                    try:
                                        UserProfileManager(self.env).remove_user_file(user_file_old)
                                    except Exception, e:
                                        self.log.error(e)
                                        data['errors'].append(_("Unable to remove previous %s=[%s]")%(field, user_file_old))
                        elif data['um_profile_fields'][field]['type']=='multichecks':
                            user[field] = '|'.join(req.args.getlist("um_profile_%s"%(field)))
                        else:
                            user[field] = req.args.get("um_profile_%s"%(field))
                    elif data['um_profile_fields'][field]['type']=='multichecks':
                        # cleanup if none selected
                        user[field]=''

                if user.save():
                    data['messages'].append(_("Successfully updated profile for user [%s].")%(user.username))
        
        add_stylesheet(req, 'tracusermanager/css/admin_um_profile.css')
        
        return 'admin_um_profile.html', data    

    # IUserListCellContributor methods
    def get_userlist_cells(self):
        yield ('name', _('Name'),0)
        yield ('email', _('Email'),1)
        yield ('role', _('Role'),2)
        
    def render_userlist_cell(self, cell_name, user):
        """Should render user cell"""
        #if cell_name in ('name', 'email', 'role'):
        return user[cell_name]
        #return None