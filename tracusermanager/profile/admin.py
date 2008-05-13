# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.web.chrome import add_stylesheet, add_script
from trac.util.text import to_unicode
from trac.util.translation import _

from tracusermanager.profile.api import UserProfileManager


class UserProfileFieldsAdminPage(Component):
    
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('accounts', _('Accounts'), 'xum_profile_fields', _('User Profile Fields'))

    def render_admin_panel(self, req, cat, page, path_info):
        #assert req.perm.has_permission('TRAC_ADMIN')
        #req.perm.assert_permission('TRAC_ADMIN')
        
        def _field_from_req(self, req):
            cfdict = {'name': to_unicode(req.args.get('name')),
                      'label': to_unicode(req.args.get('label')),
                      'type': to_unicode(req.args.get('type')),
                      'value': to_unicode(req.args.get('value')),
                      'options': [x.strip() for x in to_unicode(req.args.get('options')).split("\n")],
                      'cols': to_unicode(req.args.get('cols')),
                      'rows': to_unicode(req.args.get('rows')),
                      'order': req.args.get('order', 0),
                      'internal': req.args.get('internal', 0)
                      }
            return cfdict
        
        cfadmin = {} # Return values for template rendering
        cfadmin['SUPPORTED_TYPES'] = UserProfileManager(self.env).SUPPORTED_FIELD_TYPES
        
        # Detail view?
        if path_info:
            
            currentcf = UserProfileManager(self.env).get_user_profile_fields(False).get(path_info, False).copy()
            if not currentcf:
                raise TracError("Profile field %s does not exist." % path_info)
            
            if req.method == 'POST':
                if req.args.get('save'):
                    cfdict = _field_from_req(self, req) 
                    UserProfileManager(self.env).update_user_profile_field(cfdict)
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            
            if currentcf.has_key('options'):
                optional_line = ''
                if '' in currentcf['options']:
                    optional_line = '\n'
                currentcf['options'] = optional_line + "\n".join(currentcf['options'])
            
            cfadmin['customfield'] = currentcf
            cfadmin['display'] = 'detail'
            
        else:
            if req.method == 'POST':
                # Add Custom Field
                if req.args.get('add') and req.args.get('name'):
                    cfdict = _field_from_req(self, req)
                    UserProfileManager(self.env).update_user_profile_field(cfdict, create=True)
                    req.redirect(req.href.admin(cat, page))
                    
                         
                # Remove Custom Field
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No custom field selected'
                    for name in sel:
                        UserProfileManager(self.env).delete_user_profile_field({'name': name})
                    
                    req.redirect(req.href.admin(cat, page))

                elif req.args.get('apply'):
                    # Change order
                    
                    order = dict([(key[6:], req.args.get(key)) for key
                                  in req.args.keys()
                                  if key.startswith('order_')])
                    values = dict([(val, True) for val in order.values()])
                    if len(order) != len(values):
                        raise TracError, 'Order numbers must be unique.'
                    cf = UserProfileManager(self.env).get_user_profile_fields(False)
                    for cur_cf_name, cur_cf in cf.items():
                        cur_cf['order'] = order[cur_cf_name]
                        UserProfileManager(self.env).update_user_profile_field(cur_cf)
                    req.redirect(req.href.admin(cat, page))

            cf_list = []
            for item, attributes in UserProfileManager(self.env).get_user_profile_fields(False).items():               
                attributes['href'] = req.href.admin(cat, page, attributes['name'])
                cf_list.append(attributes)
            
            cfadmin['customfields'] = sorted(cf_list, lambda x,y:x['order']-y['order'])
            cfadmin['display'] = 'list'
            
        return ('admin_um_profile_fields.html', {'cfadmin': cfadmin})
