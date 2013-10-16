import sha, shelve, time, os
from dbUtil import GetEngine

SESSION_FILE_DIR = '***REMOVED***/fp/sessions'

class Session(object):
    def __init__(self, forceNew=False, sid=None, timeout=300, expires=1000000):
    #------------------------------------------------------------------
        self.mTimeout = timeout
        
        # set sid or create new one:
        if not forceNew and sid:
            self.mSid = sid
        else:
            self.mSid = sha.new(repr(time.time())).hexdigest()

        # get and create if necessary session storage dir:
        #session_dir = os.environ['DOCUMENT_ROOT'] + SESSION_FILE_DIR
        session_dir = os.getenv('SESSION_FILE_DIR', SESSION_FILE_DIR)
        if not os.path.exists(session_dir):
            try:
                os.mkdir(session_dir, 02770)
            # If the apache user can't create it manually
            except OSError, e:
                errmsg =  """%s when trying to create the session directory. Create it as '%s'""" % (e.strerror, os.path.abspath(session_dir))
                raise OSError, errmsg
        # create  or open session file:
        sessFile = session_dir + '/sess_' + self.mSid
        self.data = shelve.open(sessFile, writeback=True)
        os.chmod(sessFile, 0660)
        
        # Initialize the dbsession:
        # Note the dbsess doesn't get saved in the shelf, we must reconnect each time.
        #if not forceNew: self.mDBsess = dbUtil.GetEngine(self)

 
    def close(self): 
    #------------------------------------------------------------------
        self.data.close()

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


