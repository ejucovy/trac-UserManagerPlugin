# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

import traceback 
import os
import re
from StringIO import StringIO

from trac.attachment import Attachment
from trac.core import *
from trac.config import Option
from trac.util.translation import _
from trac.util.text import unicode_unquote
from trac.util import get_reporter_id
from trac.wiki import WikiPage

class IUserProfilesListMacroCellContributor(Interface):
    
    def get_userlistmacro_cells(self):
        """Should return a list of provided cells in form of
        [ ('cell_name', _('Cell Label')) ]
        """
        
    def render_userlistmacro_cell(self, cell_name, user):
        """Should render user cell"""


def parse_custom_fields_config(rawfields):
    """ """
    fields = {}
    for option, value in rawfields:
        parts = option.split('.')
        field = parts[0]
        if field not in fields:
            fields[field] = {}
        if len(parts) == 1:
            fields[field]['type']=value
        else:
            fields[field][parts[1]] = value
    
    # Fill default values
    for field, attributes in fields.items():
        if 'name' not in attributes:
            attributes['name'] = field

        if 'label' not in attributes:
            attributes['label'] = field

        if 'value' not in attributes:
            attributes['value'] = ''
        
        if 'order' not in attributes:
            attributes['order'] = -1
            
        if 'options' not in attributes:
            attributes['options'] = []
        else:
            attributes['options'] = attributes['options'].split('|')

        if 'cols' not in attributes:
            attributes['cols'] = 20

        if 'rows' not in attributes:
            attributes['rows'] = 20

        if 'internal' not in attributes:
            attributes['internal'] = 0

    return fields
    
def get_custom_fields_config(config, section_name):
    return parse_custom_fields_config(list(config.options(section_name)))

class UserProfileManager(Component):
    
    
    attachments_wikiPage = Option('user_manager', 'wiki_page_attachment', 'UserManagerPluginPictures',
        """Wiki Page used by TracUserManager plugin to manage 
        UserProfile's picture.""")
    
    SUPPORTED_FIELD_TYPES = ['text', 'select', 'multichecks', 'textarea', 'wikitext']
    CONFIG_SECTION_NAME = 'um_profile-custom'
    
    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        
        self.fields={  'name':dict(name='name', type='text',label=_('Name'), value='', order=-3, cols=20),
                       'email':dict(name='email', type='text',label=_('Email'), value='', order=-2, cols=20 ),
                       'role':dict(name='role', type='text',label=_('Role'), value='', order=-1, cols=20 ),
                       'picture_href':dict(name='picture_href',type='file',label=_('Picture'), value='', order=0 )}
    
        for field, attributes in get_custom_fields_config(self.config, self.CONFIG_SECTION_NAME).items():
            if attributes['order']==-1:
                attributes['order']=len(self.fields)
            else:
                attributes['order']=int(attributes['order'])
            self.fields[field] = attributes
    
    def get_user_profile_fields(self, all=True, ignore_internal=False):
        if all:
            if ignore_internal:
                return dict(filter(lambda x:int(x[1].get('internal','0'))==0, self.fields.items()))
            return self.fields
        else:
            return dict(filter(lambda x:not x[0] in ['name','email','role','picture_href'],self.fields.items()))
    
    def update_user_profile_field(self, field, create=False):
        """ Update or create a new user profile field (if requested).
        field is a dictionary with the following possible keys:
            name = field's name
            type = text|checkbox|select|radio|textarea
            label = label description
            value = default value for field content
            options = options for select and multichecks types (list, leave first empty for optional)
            cols = number of columns for text area/wikitext
            rows = number of rows for text area/wikitext
            order = specify sort order for field
            internal = if True than field will be visible only on the admin page.
        """
        
        # setting environment
        env = self.env
        
        # Name, Type and Label is required
        if not (field.has_key('name') and field.has_key('type') and field.has_key('label')):
            raise TracError("Custom field needs at least a name, type and label.")
        
        # Only alphanumeric characters (and [-_]) allowed for custom fieldname
        matchlen = re.search("[a-z0-9-_]+", field['name']).span()
        namelen = len(field['name'])
        if (matchlen[1]-matchlen[0] != namelen):
            raise TracError("Only alphanumeric characters allowed for custom field name (a-z or 0-9 or -_).")
        
        # If Create, check that field does not already exist
        if create and env.config.get(self.CONFIG_SECTION_NAME, field['name']):
            raise TracError("Can not create as field already exists.")
        
        # Check that it is a valid field type
        if not field['type'] in self.SUPPORTED_FIELD_TYPES:
            raise TracError("%s is not a valid field type" % field['type'])
        
        # Create/update the field name and type
        env.config.set(self.CONFIG_SECTION_NAME, field['name'], field['type'])
        
        # Set the field label
        env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.label', field['label'])
        
        # Set default value if it exist in dictionay with value, else remove it if it exists in config
        if field.has_key('value') and field['value']:
            env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.value', field['value'])
        elif env.config.get(self.CONFIG_SECTION_NAME, field['name'] + '.value'):
            env.config.remove(self.CONFIG_SECTION_NAME, field['name'] + '.value')
       
        # If select or radio set options, or remove if it exists and field no longer need options
        if field['type'] in ['select', 'multichecks']:
            if not field.has_key('options') or field['options'] == []:
                raise TracError("No options specified for %s field" % field['type'])
            env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.options', '|'.join(field['options']))
        elif env.config.get(self.CONFIG_SECTION_NAME, field['name'] + '.options'):
            env.config.remove(self.CONFIG_SECTION_NAME, field['name'] + '.options')
       
        # Set defaults for textarea if none is specified, remove settings if no longer used
        env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.cols', field['cols'])
        env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.rows', field['rows'])
        
        # internal ?
        env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.internal', field.get('internal',0))
        
         # Set sort setting if it is in customfield dict, remove if no longer present
        if create:
            last = len(self.get_user_profile_fields(False))+1
            env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.order',
                    field.get('order',0) or last)
        elif field.has_key('order') and field['order']:
            # Exists and have value - note: will not update order conflicting with other fields
            if str(field['order']).isdigit():
                env.config.set(self.CONFIG_SECTION_NAME, field['name'] + '.order', field['order'])
        elif env.config.get(self.CONFIG_SECTION_NAME, field['name'] + '.order'):
            env.config.remove(self.CONFIG_SECTION_NAME, field['name'] + '.order')
        
        # Save settings
        env.config.save()

    def delete_user_profile_field(self, field, config_save=True):
        """ Deletes a custom field.
        Input is a dictionary (see update_custom_field), but only ['name'] is required.
        """
        
        # setting env
        env = self.env
        
        if not env.config.get(self.CONFIG_SECTION_NAME, field['name']):
            return 
        
        # Need to redo the order of fields that are after the field to be deleted
        order_to_delete = env.config.getint(self.CONFIG_SECTION_NAME, field['name']+'.order')
        cfs = self.get_user_profile_fields(False)
        for profile_field_name, profile_field in cfs.items():
            if profile_field['order'] > order_to_delete:
                env.config.set(self.CONFIG_SECTION_NAME, profile_field['name']+'.order', profile_field['order'] -1 )
        
        # Remove any data for the custom field (covering all bases)
        env.config.remove(self.CONFIG_SECTION_NAME, field['name'])
        for attribute_name in ['.name', '.type', '.label', '.value', '.options', '.cols', '.rows', '.order', '.internal']:
            env.config.remove(self.CONFIG_SECTION_NAME, field['name']+attribute_name)

        # Save settings
        if config_save:
            env.config.save()

    def get_uploaded_file_href(self, req, user, field, req_field):
        """Returns uploaded file's url
        
        @param req: trac.web.req
        @param user: tracusermanager.api.User
        @param field: str
        @param req_field: str 
        @return: str
        """
        
        # validate request field
        upload = req.args.get(req_field, None)
        if upload == None or not hasattr(upload, 'filename') or not upload.filename:
            return user[field]
        
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2) # seek to end of file
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError(_("Can't upload empty file"))

        filename = upload.filename
        filename = filename.replace('\\', '/').replace(':', '/')        
        filename = os.path.basename(filename)
        
        if not filename:
            raise TracError(_('No file uploaded'))
        
        page = WikiPage(self.env,  self.attachments_wikiPage)
        if not page.exists:
            page.text="= UserManager's Attachments ="
            page.save( 'trac', 'Page created by tracusermanager.profile component',  req.remote_addr)
       
        attachment = Attachment(self.env, 'wiki', self.attachments_wikiPage)
        attachment.author = get_reporter_id(req, 'author')
        attachment.ipnr = req.remote_addr
        attachment.description = (_("%s\'s Avatar") % (user.username))
        attachment.insert('_'.join([user.username, filename]), upload.file, size)
        
        return req.href('/'.join(['raw-attachment', 'wiki',self.attachments_wikiPage, attachment.filename]))
    
    def remove_user_file(self, file_href):
        """Returns uploaded file's url
        
        @param file_href: str
        @return: bool
        """
        try:
            Attachment(self.env, 'wiki', self.attachments_wikiPage, filename=unicode_unquote(file_href.split('/')[-1]) ).delete()
            return True
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError(_("Unable to remove file. [%s].")%(file_href))
            return False

