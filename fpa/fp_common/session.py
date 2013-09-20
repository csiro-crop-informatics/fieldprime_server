import sha, shelve, time, Cookie, os
import dbUtil

SESSION_FILE_DIR = '***REMOVED***/fp/sessions'

class Session(object):
   def __init__(self, forceNew=False, timeout=300, expires=1000000, cookie_path='/'):
   #------------------------------------------------------------------
      self.mTimeout = timeout
      string_cookie = os.environ.get('HTTP_COOKIE', '')
      self.cookie = Cookie.SimpleCookie()
      self.cookie.load(string_cookie)   # create from cookie passed by browser

      # get sid from cookie or create new one:
      if not forceNew and self.cookie.get('sid'):
         sid = self.cookie['sid'].value
         # Clear session cookie from other cookies
         self.cookie.clear()
      else:
         self.cookie.clear()
         sid = sha.new(repr(time.time())).hexdigest()

      self.cookie['sid'] = sid

      if cookie_path:
         self.cookie['sid']['path'] = cookie_path

      # get and create if necessary session storage dir:
      #session_dir = os.environ['DOCUMENT_ROOT'] + SESSION_FILE_DIR
      session_dir = SESSION_FILE_DIR
      if not os.path.exists(session_dir):
         try:
            os.mkdir(session_dir, 02770)
         # If the apache user can't create it create it manually
         except OSError, e:
            errmsg =  """%s when trying to create the session directory. Create it as '%s'""" % (e.strerror, os.path.abspath(session_dir))
            raise OSError, errmsg
      # create  or open session file:
      sessFile = session_dir + '/sess_' + sid
      self.data = shelve.open(sessFile, writeback=True)
      os.chmod(sessFile, 0660)
      
      # Initializes the expires data:
      if not self.data.get('cookie'):
         self.data['cookie'] = {'expires':''}
      self.set_expires(expires)

      # Initialize the dbsession:
      # Note the dbsess doesn't get saved in the shelf, we must reconnect each time.
      #if not forceNew: self.mDBsess = dbUtil.GetEngine(self)

 
   def close(self): 
   #------------------------------------------------------------------
      self.data.close()

   def set_expires(self, expires=None):
   #------------------------------------------------------------------
   # Set expires in both cookie and shelf
      if expires == '':
         self.data['cookie']['expires'] = ''
      elif isinstance(expires, int):
         self.data['cookie']['expires'] = expires
         
      self.cookie['sid']['expires'] = self.data['cookie']['expires']


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

   #def SetDBSession(self):
   #------------------------------------------------------------------
   #   self.dbsess = dbUtil.GetSession()

   def DB(self):
   #------------------------------------------------------------------
      if not hasattr(self, 'mDBsess'):
         self.mDBsess = dbUtil.GetEngine(self)
      return self.mDBsess


# Static Methods:
# Not used I think
def GetSessionData():
   string_cookie = os.environ.get('HTTP_COOKIE', '')
   self.cookie = Cookie.SimpleCookie()
   self.cookie.load(string_cookie)   # create from cookie passed by browser

   # get sid from cookie or create new one:
   if self.cookie.get('sid'):
      sid = self.cookie['sid'].value
         # Clear session cookie from other cookies
      self.cookie.clear()
   else:
      return False
      
   self.cookie['sid'] = sid
   if cookie_path:
      self.cookie['sid']['path'] = cookie_path

   # get and create if necessary session storage dir:
   session_dir = os.environ['DOCUMENT_ROOT'] + '/session'
   if not os.path.exists(session_dir):
      try:
         os.mkdir(session_dir, 02770)
         # If the apache user can't create it create it manualy
      except OSError, e:
         errmsg =  """%s when trying to create the session directory. Create it as '%s'""" % (e.strerror, os.path.abspath(session_dir))
         raise OSError, errmsg
   # create  or open session file:
   sessFile = session_dir + '/sess_' + sid
   self.data = shelve.open(sessFile, writeback=True)
   os.chmod(sessFile, 0660)
      
   # Initializes the expires data
   if not self.data.get('cookie'):
      self.data['cookie'] = {'expires':''}
   self.set_expires(expires)
