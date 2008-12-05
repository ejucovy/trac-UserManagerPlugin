# -*- coding: iso-8859-1 -*-
#
# Copyright 2008 Optaros, Inc.
#
try:
    import threading
except ImportError:
    import dummy_threading as threading
import time

import traceback 
import time
from StringIO import StringIO

from trac.core import *
from trac.config import *
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider

class IUserAttributeChangeListener(Interface):

    def user_attribute_changed(username, attribute, old_value, new_value): 
        """
        Called when a user attribute changes.
        """

class User(object):
    """Object representing a user"""
    
    def __init__(self, username=None, user_manager=None, **attr):
        self.username = username
        self.user_manager = user_manager
        self.default_attributes = attr
        self.changes = {}
        self.deleted = {}
        
    def exists(self):
        """Return true if user exists."""
        if self.store:
            return len(self.user_manager.search_users(self.username))>0
        return False

    def __getitem__(self, attribute):
        """Gets user attribute.
        
        @param name: str
        """
        if self.changes.has_key(attribute):
            return self.changes[attribute]
        if self.user_manager:
            value = self.user_manager.get_user_attribute(self.username, attribute)
            if value:
                return value
        if self.default_attributes.has_key(attribute):
            return self.default_attributes[attribute]      
            
        return None
        
    def __setitem__(self, attribute, value):
        """Sets user attribute.
        
        @param name: str
        @param value: str
        """
        self.changes[attribute] = value
    
    def __delitem__(self, attribute):
        """Removes user attribute.
        
        @param name: str
        """
        self.deleted[attribute] = 1
    
    def save(self):
        return self.user_manager.save_user(self)
        
class IUserStore(Interface):
    
    def get_supported_user_operations(username):
        """Returns supported operations 
        in form of [operation, ].
        
        @return: list"""
    
    def execute_user_operation(operation, user, operation_arguments):
        """Executes user operation.
        
        @param operation: str
        @param user: tracusermanager.api.User
        @param operation_arguments: dict"""
    
    def create_user(username):
        """Creates an user.
        Returns True if succeeded.
        
        @param user: str
        @return: bool"""
        
    def search_users(user_pattern):
        """Returns a list of user names that matches user_pattern.
        
        @param user_pattern: str
        @return: list"""
    
    def delete_user(username):
        """Deletes an user.
        Returns True if the delete operation succeded.
        
        @param user: str
        @return: bool"""

class IAttributeProvider(Interface):
    
    def get_user_attribute(username, attribute):
        """Returns user's attributes.
        
        @param username: str
        @param attribute: str"""
    
    def set_user_attribute(username, attribute, value):
        """Sets user's attribute value.
                
        @param username: str 
        @param attribute: str
        @param value: str
        @return: bool
        """
    
    def delete_user_attribute(username, attribute):
        """Removes user attribute
        
        @param username: str
        @param attribute: str
        @return: bool 
        """
    
    def get_usernames_with_attributes(attributes_dict):
        """Returns a list of usernames 
        that have "user[attributes_dict.keys] like attributes_dict.values".
        
        @param attributes_dict: str
        @return: list"""

class UserManager(Component):
    
    implements(ITemplateProvider)
    
    user_store = ExtensionOption('user_manager', 'user_store', IUserStore,
                            'SessionUserStore',
        """Name of the component implementing `IUserStore`, which is used
        for storing project's team""")

    attribute_provider = ExtensionOption('user_manager', 'attribute_provider', IAttributeProvider,
                            'SessionAttributeProvider',
        """Name of the component implementing `IAttributeProvider`, which is used
        for storing user attributes""")

    change_listeners = ExtensionPoint(IUserAttributeChangeListener)
    
    # Public methods
    def get_user(self, username):
        return User(username, self)

    def get_active_users(self):
        """Returns a list with the current users(team)
        in form of [tracusermanager.api.User, ]
        
        @return: list"""
        return self.search_users()
    
    def save_user(self, user):  
        for attribute, value in user.changes.items():
            self.set_user_attribute(user.username, attribute, value)
        for attribute in user.deleted.keys():
            self.delete_user_attribute(user.username, attribute)
        return True
        
    # Public methods : IUserStore 
    def get_supported_user_operations(self, username):
        return self.user_store.get_supported_user_operations(username)
    
    def execute_user_operation(operation, user, operation_arguments):
        return self.user_store.execute_user_operation(operation, user, operation_arguments)
    
    def create_user(self, user):
        if user.username is None:
            raise TracError(_("Username must be specified in order to create it"))
        if self.user_store.create_user(user.username):
            user_attributes = user.default_attributes
            user_attributes.update(user.changes)
            for attribute, value in user_attributes.items():
                self.set_user_attribute(user.username, attribute, value)
            return True
        return False
        
    def search_users(self, user_templates=[]):
        """Returns a list of users matching 
        user_templates."""
        search_result = {}
        templates=[]
        
        if isinstance(user_templates, str):
            templates = [User(user_templates)]
        elif not isinstance(user_templates, list):
            templates = [user_templates]
        else:
            templates = user_templates
        
        if len(templates)==0:
            # no filters are passed so we'll return all users
            return [ self.get_user(username)
                        for username in self.user_store.search_users()]
        
        # search 
        search_candidates = []
        for user_template in templates:
            # by username
            if user_template.username is not None:
                search_result.update([ (username,self.get_user(username)) 
                                          for username in self.user_store.search_users(user_template.username)])
            else:
                search_attrs = user_template.default_attributes.copy()
                search_attrs.update(user_template.changes.copy())
                search_attrs.update(enabled='1')            
                search_result.update([ (username, self.get_user(username))
                                        for username in self.attribute_provider.get_usernames_with_attributes(search_attrs)])
                
        return search_result.values()
        
    def delete_user(self, username):
        try:
            from acct_mgr.api import AccountManager
            if AccountManager(self.env).has_user(username):
                AccountManager(self.env).delete_user(username)
        except Exception, e:
            self.log.error("Unable to delete user's authentication details")
        return self.user_store.delete_user(username)

    # Public methods : IAttributeStore 
    def get_user_attribute(self, username, attribute):
        return self.attribute_provider.get_user_attribute(username, attribute)

    def set_user_attribute(self, username, attribute, value):
        oldval = self.attribute_provider.get_user_attribute(username, attribute)
        retval = self.attribute_provider.set_user_attribute(username, attribute, value)
        for listener in self.change_listeners:
            listener.user_attribute_changed(username, attribute, oldval, value)
        return retval

    def delete_user_attribute(self, username, attribute):
        oldval = self.attribute_provider.get_user_attribute(username, attribute)
        retval = self.attribute_provider.delete_user_attribute(username, attribute)
        for listener in self.change_listeners:
            listener.user_attribute_changed(username, attribute, oldval, None)
        return self.attribute_provider.delete_user_attribute(username, attribute)
    
    def get_usernames_with_attributes(self, attribute_dict):
        return self.attribute_provider.get_usernames_with_attributes(attribute_dict)
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracusermanager', 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracusermanager', resource_filename(__name__, 'htdocs'))] 



class SessionUserStore(Component):
    
    implements(IUserStore)
    
    def get_supported_user_operations(self, username):
        return []
        
    def execute_user_operation(self, operation, user, operation_arguments):
        return True
    
    def create_user(self, username):
        db = self.env.get_db_cnx()
       
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO session (sid, last_visit, authenticated)"
                           " VALUES(%s,%s,1)", [username, int(time.time())])
            db.commit()
        except Exception, e:
            db.rollback()
            self.log.debug("Session for %s exists, no need to re-create it."%(username))
            
        cursor = db.cursor()
        try:
            # clean up 
            cursor.execute("DELETE "
                               "FROM session_attribute "
                               "WHERE sid=%s and authenticated=1 and name='enabled'", [username])
            
            # register active user 
            cursor.execute("INSERT "
                               "INTO session_attribute "
                               "(sid,authenticated,name,value) "
                               "VALUES(%s,1,'enabled','1')", [username])
            # and .. commit
            db.commit()
            return True
        
        except Exception, e:
            db.rollback()
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError(_("Unable to create user [%s].")%(username))
            return False
        
    def search_users(self, username_pattern=None):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        search_result = []
        
        try:
            if username_pattern is None:
                cursor.execute("SELECT sid FROM session_attribute "
                                   "WHERE name='enabled' and value='1'")
            else:
                cursor.execute("SELECT sid FROM session_attribute "
                               "WHERE sid like %s "
                                   "and name='enabled' "
                                   "and value='1'", (username_pattern,))
            for username, in cursor:
                search_result.append(username)
            
            
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError(_("Unable to find username from pattern [%s].")%(username_pattern))
        
        return search_result
            
    def delete_user(self, username):
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        try:
            cursor.execute("DELETE "
                               "FROM session_attribute "
                               "WHERE sid=%s and name='enabled'", (username,))
            db.commit()
            return True
        
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError(_("Unable to delete user [%s].")%(username))
            return False
        
class SessionAttributeProvider(Component):
    implements(IAttributeProvider)
    
    def get_user_attribute(self, username, attribute):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT value "
                           "FROM session_attribute "
                           "WHERE sid=%s and name=%s ", (username, attribute))
            
            _result = list(cursor)
            if len(_result)>0:
                return _result[0][0]
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError(_("Unable to load attribute %s for user [%s].")%(attribute, username))    
               
        return None
    
    def set_user_attribute(self, username, attribute, value):
        """Sets user's attribute value.
                
        @param username: str 
        @param attribute: str
        @param value: str
        @return: bool
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        try:
            
            cursor.execute("DELETE FROM session_attribute "
                               "WHERE sid=%s and name=%s", (username, attribute))
            
            cursor.execute("INSERT INTO session_attribute "
                               "(sid, authenticated, name, value) VALUES (%s, 1, %s, %s)",
                               (username, attribute, value))
            db.commit()
            
            return True
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError("Unable to set attribute %s for user [%s]."%(attribute, username))
    
        return False
    
    def delete_user_attribute(self, username, attribute):
        """Removes user attribute.
        
        @param username: str
        @param attribute: str
        @return: bool 
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        try:
            
            cursor.execute("DELETE FROM session_attribute "
                               "WHERE sid=%s and name=%s", (username, attribute))            
            db.commit()
            
            return True
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            raise TracError("Unable to delete attribute %s for user [%s]."%(attribute, username))
        
        return False

    def get_usernames_with_attributes(self, attributes_dict=None):
        """ Returns all usernames matching attributes_dict.
        
        Example: self.get_usernames_with_attributes(dict(name='John%', email='%'))
        
        @param attributes_dict: dict
        @return: list
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        try:                     
            if attributes_dict is None:
                cursor.execute("SELECT sid FROM session_attribute WHERE name='enabled'")
            else:
                """ The following line executes a query that should look like this:
                
                    #for attributes_dict = dict(name='John%', email='%@exemple.com')):
                        SELECT  sid
                        FROM session_attribute 
                        WHERE name='name' AND value like 'John%' 
                           OR name='email' AND value like '%@exemple.com' 
                        GROUP BY sid 
                        HAVING count(*)=2           
                """
                
                # dict to list attr_dict = { k1:v1, k2:v2, ... } -> [k1,v1,k2,v2..., len(attr_dict)]
                attributes_list=[]
                for k, v in attributes_dict.items():
                    attributes_list.append(k.startswith('NOT_') and k[4:] or k)
                    attributes_list.append(v)
                    
                attributes_list.append(len(attributes_dict))
                
                def _get_condition(k,v):
                    return "name=%s AND value " + (k.startswith('NOT_') and 'NOT' or '') + " LIKE %s"
                    
                cursor.execute("SELECT sid"
                               " FROM session_attribute"
                               " WHERE " + " OR ".join([ _get_condition(k,v) for k,v in attributes_dict.items()]) +
                               " GROUP BY sid"
                               " HAVING count(*)=%s", attributes_list)
            return [id for id, in cursor]
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            return []

class CachedSessionAttributeProvider(SessionAttributeProvider):
    CACHE_UPDATE_INTERVAL = 50
    
    def __init__(self):
        self._attribute_cache = {}
        self._attribute_cache_last_update = {}
        self._attribute_cache_lock = threading.RLock()

    def _update_cache(self, username, force=False):
        self._attribute_cache_lock.acquire()
        try:
            now = time.time()
            if now > self._attribute_cache_last_update.get(username,0) + CachedSessionAttributeProvider.CACHE_UPDATE_INTERVAL \
                    or not self._attribute_cache.has_key(username) \
                    or force:
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute("SELECT name, value FROM session_attribute WHERE sid=%s",(username,))
                self._attribute_cache[username] = {}
                for name,value in cursor:
                    self._attribute_cache[username][name] = value
                self._attribute_cache_last_update[username] = now
                self.log.debug("Updating SessionAttributeProvider attribute cache for user <%s>"%(username,))
        finally:
            self._attribute_cache_lock.release()
    
    def get_user_attribute(self, username, attribute):
        self._update_cache(username)
        if username in self._attribute_cache:
            return self._attribute_cache[username].get(attribute)
        return None
    
    def set_user_attribute(self, username, attribute, value):
        return_value = super(CachedSessionAttributeProvider, self).set_user_attribute(username, attribute, value)
        self._update_cache(username, force=True)
        return return_value
        
    def delete_user_attribute(self, username, attribute):
        return_value = super(CachedSessionAttributeProvider, self).delete_user_attribute(username, attribute)
        self._update_cache(username, force=True)
        return return_value

class EnvironmentFixKnownUsers(Component):
    implements(IEnvironmentSetupParticipant)
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        pass
    
    def environment_needs_upgrade(self, db):
        def inline_overwrite_get_known_users(environment = None, cnx=None):
            users = UserManager(self.env).get_active_users()
            if len(users)>0:
                for user in users:
                    yield (user.username, user['name'], user['email'])
            else:
                # No users defined, so we're returning the original list
                for user, name, email in  self.env.__class__.get_known_users(self.env):
                    yield (user, name, email)
        
        self.env.get_known_users = inline_overwrite_get_known_users
        
        return False    

    def upgrade_environment(self, db):
        pass
