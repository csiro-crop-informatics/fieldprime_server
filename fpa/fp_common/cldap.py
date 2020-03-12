# cldap.py
#
# Code of unknown origin, given to me (Michael Kirk) by Raj Gaire.
# Now somewhat modified.


import ldap

# Details scrubbed and will need to be set for use.
SERVER_URL = ''
search_dn = ''
search_password = ''
ACTIVE_BASE=''
CEASED_BASE=''

scope = ldap.SCOPE_SUBTREE
attrs = ['givenName', 'sn', 'cn', 'division', 'mail']

class LdapUser(object):
        def __init__(self, conn, dn, ceased, entry):
                self._conn = conn
                self._dn = dn
                self.ceased = ceased

                # TODO: change following to a list comprehension?
                if 'givenName' in entry:
                        self.given_name = entry['givenName'][0]
                if 'sn' in entry:
                        self.surname = entry['sn'][0]
                if 'cn' in entry:
                        self.ident = entry['cn'][0]
                if 'division' in entry:
                        self.division = entry['division'][0]
                if 'mail' in entry:
                        self.email_address = entry['mail'][0]

                if 'givenName' in entry and 'sn' in entry:
                        self.name = entry['givenName'][0] + ' ' + entry['sn'][0]

        def authenticate(self, credentials):
                if self.ceased:
                        return False

                try:
                        self._conn.simple_bind_s(self._dn, credentials)
                        return True
                except ldap.INVALID_CREDENTIALS:
                        return False

        def __str__(self):
                attrs = dict([(k, getattr(self, k)) for k in ['given_name', 'surname', 'name', 'division', 'email_address'] if hasattr(self, k)])
                return '{0} (ceased={1}, {2})'.format(self.ident, self.ceased, attrs)

class LdapServer(object):
        # TODO: better handling of configuration and defaults.
        def __init__(self, url, active_base=ACTIVE_BASE, ceased_base=CEASED_BASE):
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

                self.url = url

                self.active_base = active_base
                self.ceased_base = ceased_base

                self._state = 'disconnected'

                try:
                        self._connect()
                except ldap.SERVER_DOWN as e:
                        pass # If we cannot connect now, attempt lazy-connection later.

        def _connect(self):
                conn = ldap.initialize(self.url)
                conn.set_option(ldap.OPT_REFERRALS, 0)
                conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
                conn.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
                conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
                conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
                self._conn = conn

                self._conn.simple_bind_s(search_dn, search_password)

        def _search_wrapper (self, search_base, filter):
                try:
                        return self._search(search_base, filter)
                except ldap.SERVER_DOWN as e:
                        #print 'Server down. Attempting to reconnect...'
                        self._connect()
                        return self._search(search_base, filter)

        def _search (self, search_base, filter):
                result = []

                for name, entry in self._conn.search_s(search_base, ldap.SCOPE_SUBTREE, filter, attrs):
                        result.append(LdapUser(self._conn, name, search_base == self.ceased_base, entry))

                return result

        def find(self, *args, **kwargs):
                # Disallow ceased results by default.
                allow_ceased = 'allow_ceased' in kwargs and kwargs['allow_ceased']

                # TODO: this could be a lot more clever...
                filter = '(objectClass=user)'
                if len(args) == 1:
                        filter = '(&(|(cn={0}*)(sn={0}*)(givenName={0}*))(objectClass=user))'.format(args[0])
                elif 'ident' in kwargs:
                        filter = '(&(cn={0}*)(objectClass=user))'.format(kwargs['ident'])
                elif 'surname' in kwargs:
                        filter = '(&(surname={0}*)(objectClass=user))'.format(kwargs['surname'])
                elif 'given_name' in kwargs:
                        filter = '(&(givenName={0}*)(objectClass=user))'.format(kwargs['given_name'])

                results = self._search_wrapper(self.active_base, filter)

                if allow_ceased and self.ceased_base:
                        results.extend(self._search_wrapper(self.ceased_base, filter))

                return results

        def getUserByIdent(self, ident):
                # MK addition - get single user by ident.
                # NB we don't get "ceased"
                # Return None if no results or more than one.
                # MFK should raise exception for error cond.
                filter = '(&(cn={0}*)(objectClass=user))'.format(ident)
                try:
                        results = self._search_wrapper(self.active_base, filter)
                except Exception as e:
                        return None
                if len(results) == 1:
                        return results[0]
                else:
                        None

class Error(Exception):
        pass

def getUserName(ident):
#----------------------------------------------------------------
# Returns fullname of user with given ident if they exist.
# Returns None if no such user.
# Raises NexusException is appropriate.
#
        # Check nexus user exists, and get name:
        ldapServer = LdapServer(SERVER_URL)
        if not ldapServer:
                raise Error('Cannot connect to nexus server')
        ldapUser = ldapServer.getUserByIdent(ident)
        if ldapUser is None:
                return None
        return ldapUser.given_name + ' ' + ldapUser.surname

