# -*- coding: iso-8859-1 -*-
#
# Copyright 2008 Optaros, Inc.
#

from trac.core import *
from trac.util.html import html
from trac.util.translation import _
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.web.chrome import Chrome, add_stylesheet, add_script

from tracusermanager.api import UserManager, User
from tracusermanager.profile.api import UserProfileManager, IUserProfilesListMacroCellContributor

class UserProfilesListMacro(WikiMacroBase):
    """Returns project's team roster.
        
    Usage:
        {{{ 
        
        [[UserProfilesList]]                                    # Without arguments returns current active user profiles (with enabled='1')
        [[UserProfilesList(role='developer', enabled='1')]]     # Returns all userProfiles with role='developer' and enabled='1'
        [[UserProfilesList(name='%someName%')]]                 # Returns all userProfiles with name like 'someName' 
        [[UserProfilesList({id='cbalan'},{role='%arh%'})]]      # Returns cbalan's profile and user profiles with role='%arh%' 
        [[UserProfilesList(|class=someCSS_Class, style=border:1px solid green;padding:12px)]] # Adds style and class attributes to box layout 
        
        }}}
    """
    cells_providers = ExtensionPoint(IUserProfilesListMacroCellContributor)

    def expand_macro(self, formatter, name, content):
        
        data=dict(user_profiles=[], user_profile_fields={})
        rendered_result=""
        content_args={}
        layout_args={}
        user_profile_templates=[]     
        
        # collecting arguments
        if content:    
            for i, macro_args in enumerate( content.split('|') ):
                if i == 0:
                    content_args = MacroArguments( macro_args )
                    continue
                if i == 1: 
                    layout_args = MacroArguments( macro_args )
                    break
            
            # extracting userProfile attrs 
            if len(content_args)>0:
                user_profile_templates.append(User(**content_args))
                
            if len(content_args.get_list_args())>0:
                for list_item in content_args.get_list_args():
                    user_profile_templates.append(User( **MacroArguments(list_item[1:len(list_item)-1])))
        
        # adding profiles fields description 
        data['user_profile_fields'].update(UserProfileManager(self.env).get_user_profile_fields(ignore_internal=True))

        # removing picture_href
        data['user_profile_fields'].pop('picture_href')
        
        
        def inline_wiki_to_html(text):
            return wiki_to_html(text, self.env, formatter.req)
        data['wiki_to_html'] = inline_wiki_to_html
        
        # grabbing users
        if len(user_profile_templates)>0:
            data['user_profiles'] = UserManager(self.env).search_users(user_profile_templates)
        else:
            data['user_profiles'] = UserManager(self.env).get_active_users()
        
        data['cells']=list(self._get_cells(data['user_profiles']))
        
        # add stylesheet&script
        add_stylesheet(formatter.req,'tracusermanager/css/macros_um_profile.css')
        add_script(formatter.req,'tracusermanager/js/macros_um_profile.js')
        
        # render template
        template = Chrome(self.env).load_template('macro_um_profile.html',method='xhtml')
        data = Chrome(self.env).populate_data(formatter.req, {'users':data})

        rendered_result = template.generate(**data)

        # wrap everything 
        if len(layout_args)>0:
            rendered_result= html.div(rendered_result, **layout_args)

        return rendered_result
    
    def _get_cells(self, user_list):
        for provider in self.cells_providers:
            for cell, label, order in provider.get_userlistmacro_cells():
                yield dict(name=cell, label=label, order=order, render_method = provider.render_userlistmacro_cell )

class DefaultUserProfilesListCellContributor(Component):
    implements(IUserProfilesListMacroCellContributor)
    def get_userlistmacro_cells(self):
        yield ('name', _('Name'),0)
        yield ('email', _('Email'),1)
        yield ('role', _('Role'),2)
    def render_userlistmacro_cell(self, cell_name, user):
        """Should render user cell"""
        return user[cell_name]

class TeamRosterMacro(UserProfilesListMacro):
    """Returns project's team roster.
        
    Usage:
        {{{ 
        
        [[TeamRoster]]                                    # Without arguments returns current active user profiles (with enabled='1')
        [[TeamRoster(role='developer', enabled='1')]]     # Returns all userProfiles with role='developer' and enabled='1'
        [[TeamRoster(name='%someName%')]]                 # Returns all userProfiles with name like 'someName' 
        [[TeamRoster({id='cbalan'},{role='%arh%'})]]      # Returns cbalan's profile and user profiles with role='%arh%' 
        [[TeamRoster(|class=someCSS_Class, style=border:1px solid green;padding:12px)]] # Adds style and class attributes to box layout 
        
        }}}
        
    Please use UserProfilesList macro insted of TeamRoster macro.
    Keeping this for backward compatibility with !TeamRosterPlugin.
    """
   
class MacroArguments(dict):
    
    largs=[]

    def __init__(self, arguments):
        self.largs, kwargs = parse_args(arguments)
        for k,v in kwargs.items():
            self[str(k)]=v
    
    def get_list_args(self):
        return self.largs
        
    def get_int(self, name, default=None):
        value = self.get(name, default)
        if value == '':
            return default
        try:
            return int(value)
        except Exception, e:
            return default
    
    def get_list(self, name, default=None):
        value = self.get(name, default)
        try:
            return value.split(',')
        except Exception, e:
            return defaultValue
    
    def get_dict(self, name, default=None):
        value = self.get(name, default)
        if value.startswith('{') and value.endswith('}'):
            return MacroArguments(value[1:len(value)-1])
