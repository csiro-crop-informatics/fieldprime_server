import sha, shelve, time, os
from dbUtil import GetEngine

SESSION_FILE_DIR = '***REMOVED***/fp/sessions'

# 
# WebSess
# Server side session object. Once created, a session will have an id, and state
# is stored in the file system. This may be retrieved by specifying an existing
# id on creation of WebSess object (eg the id originally created may be sent in
# a cookie stored by the browser). Sessions can report how long since last use,
# where "use" is actually a function call to set the last use time.
# The stored state includes:
# . Last use time
# . User name
# . User password
#
# It also provides a database connection, which is generated on request, using the
# stored username and password.
#
class WebSess(object):
    def __init__(self, forceNew=False, sid=None, timeout=300, sessFileDir='/tmp'):
    #------------------------------------------------------------------
        self.mTimeout = timeout
        # set sid or create new one:
        if not forceNew and sid:
            self.mSid = sid
        else:
            self.mSid = sha.new(repr(time.time())).hexdigest()

        # create if necessary session storage dir:
        if not os.path.exists(sessFileDir):
            try:
                os.mkdir(sessFileDir, 02770)
            # If the apache user can't create it manually
            except OSError, e:
                errmsg =  """%s when trying to create the session directory. Create it as '%s'""" % (e.strerror, os.path.abspath(sessFileDir))
                raise OSError, errmsg
        # create  or open session file:
        self.sessFile = sessFileDir + '/sess_' + self.mSid
        self.data = shelve.open(self.sessFile, writeback=True)
        os.chmod(self.sessFile, 0660)
        
        # Initialize the dbsession:
        # Note the dbsess doesn't get saved in the shelf, we must reconnect each time.
        #if not forceNew: self.mDBsess = dbUtil.GetEngine(self)

 
    def close(self): 
    #------------------------------------------------------------------
        sessFile = self.sessFile
        print sessFile
        self.data.close()
        os.remove(sessFile)

    def sid(self):
    #------------------------------------------------------------------
        return self.mSid

    def resetLastUseTime(self):
    #------------------------------------------------------------------
        self.data['lastvisit'] = repr(time.time())


    def getLastUseTime(self):
    #------------------------------------------------------------------
        lv = self.data.get('lastvisit')
        return float(lv) if lv else False


    def timeSinceUse(self):
    #------------------------------------------------------------------
        return float(time.time() - float(self.data.get('lastvisit')))


    def SetUserDetails(self, user, password):
    #------------------------------------------------------------------
        self.data['user'] = user
        self.data['password'] = password

    def GetUser(self):
    #------------------------------------------------------------------
        return self.data.get('user')

    def GetPassword(self):
    #------------------------------------------------------------------
        return self.data.get('password')

    def Valid(self):
    #------------------------------------------------------------------
        valid = self.data.get('user') and self.timeSinceUse() < self.mTimeout
        if valid:
            self.resetLastUseTime()
        return valid

    def DB(self):
    #------------------------------------------------------------------
        if not hasattr(self, 'mDBsess'):
            self.mDBsess = GetEngine(self)
        return self.mDBsess


