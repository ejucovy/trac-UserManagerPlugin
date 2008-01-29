# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from trac.util.translation import _
from trac.perm import PermissionSystem
from trac.web.chrome import add_stylesheet

from tracusermanager.admin import IUserManagerPanelProvider

class PermissionUserManagerPanel(Component):
    
    implements(IUserManagerPanelProvider)
    
    def get_usermanager_admin_panels(self, req):
       return [('permissions', _('Permissions'))]
    
    def render_usermanager_admin_panel(self, req, panel, user, path_info):
        user_actions = self._get_user_permissions(user)
        all_user_actions = PermissionSystem(self.env).get_user_permissions(user.username)
        actions = PermissionSystem(self.env).get_actions()+list(set([group for group, permissions in PermissionSystem(self.env).get_all_permissions()]))
        data = dict(actions=actions, 
                    all_user_actions=all_user_actions, 
                    user_actions=user_actions,
                    permsys = PermissionSystem(self.env), 
                    messages=[], errors=[])
 
        if req.method=="POST":
            updated_user_permissions = req.args.getlist('um_permission')
            
            for action in actions:
                if action in updated_user_permissions:
                    if not all_user_actions.has_key(action):
                        try: 
                            PermissionSystem(self.env).grant_permission(user.username, action)
                            data['messages'].append(_("Granted permission [%s] for user [%s].")%(action, user.username))
                        except Exception, e:
                            data['errors'].append(e)
                else:
                    if user_actions.has_key(action):
                        try:
                            PermissionSystem(self.env).revoke_permission(user.username, action)
                            data['messages'].append(_("Revoked permission [%s] for user [%s].")%(action, user.username))
                        except Exception, e:
                            data['errors'].append(e)
            if len(data['errors'])==0:
                data['messages'].append(_('Successfully updated user permissions for user [%s]')%(user.username))
                
            # Updating data
            data['user_actions'] = self._get_user_permissions(user)
            data['all_user_actions'] = PermissionSystem(self.env).get_user_permissions(user.username)

        add_stylesheet(req, 'tracusermanager/css/admin_um_permissions.css')
        
        return 'admin_um_permissions.html', data
        
    def _get_user_permissions(self, user):
        #return PermissionSystem(self.env).get_user_permissions(user.username)
        return dict([(action, True) for username, action in PermissionSystem(self.env).get_all_permissions() 
                     if username == user.username ])
