#!/usr/bin/python
#
#
#

import sys
import requests
import traceback

from const import *
#from fpRestApi import fprData

### Globals: #############################################################################

AP = 'http://0.0.0.0:5001/fpv1'
USR = 'fpadmin'
PW = 'foo'

tusr1 = 'testUser1'
tusr1pw = 'ohelfno33'

### Functions: ###########################################################################

def wout(msg):
    print '#### ', msg, ' =========================================================='
def fout(msg):
    print 'FAIL ', msg, ' =========================================================='
def fprData(jsonResponse):
    return jsonResponse["data"]
   
# # Get users:
# curl $AUTH $FP/users | prj
# 
# # Create local user:
# curl $AUTH -i -X POST -H "Content-Type: application/json" \
#      -d '{"ident":"testu1","password":"m","fullname":"Mutti Krupp","loginType":3,"email":"test@fi.fi"}' $FP/users
# 
# # Ideally here we would extract new user url from output, and use that subsequently.
# 
# # Get user:
# curl $AUTH $FP/users/testu1 | prj
# 
# # update user:
# curl $AUTH -X PUT -H "Content-Type: application/json" \
#     -d '{"fullname":"Muddy Knight", "email":"slip@slop.slap", "oldPassword":"m", "password":"secret"}' $FP/users/testu1
# 
# # get to check update:
# curl -umk:secret $FP/users/testu1 | prj
# 
# # Delete user:
# curl $AUTH -XDELETE $FP/users/testu1


def testGetProjects():
    try:
        wout('Test get /projects?all=1')
        # Get Projects using basic authentication
        url = AP + '/projects'
        params = {"all":1}
        try:
            resp = requests.get(url, timeout=5, params=params, auth=(USR, PW))
        except requests.exceptions.ConnectionError as e:
            fout("request exception: " + str(e))
            exit(0)
            
        if resp.status_code != HTTP_OK:
            fout('unexpected status: {}'.format(resp.status_code))
            return
        json = resp.json()
        data = json['data']
        print '{} projects found'.format(len(data))
        print json
    except Exception as e:
        print 'EXCEPTION in testGetProjects: ', str(e) 
        
def testGetToken():
    wout('Test get /token')  
    try:
        url = AP + '/token'
        resp = requests.get(url, timeout=5, auth=(USR, PW))
    except Exception, e:
        print 'getToken error: ' + str(e)
        return None
    if resp.status_code != HTTP_OK:
        fout('unexpected status: {}'.format(resp.status_code))
        return
    json = resp.json()
    return fprData(json)["token"]

def respError(resp):
# Print error message from api resp, if available.
    try:
        json = resp.json()
        errmsg = json['error']
        print 'API error message:' + errmsg
    except Exception as e:
        print 'Cannot get error: ' + str(e)

# # Create local user:
# curl $AUTH -i -X POST -H "Content-Type: application/json" \
#      -d '{"ident":"testu1","password":"m","fullname":"Mutti Krupp","loginType":3,"email":"test@fi.fi"}' $FP/users
# 
# # Ideally here we would extract new user url from output, and use that subsequently.
def testCreateLocalUser(token):
    wout('Test create local user /projects?all=1')
    print token
    try:
        # Get Projects using basic authentication
        url = AP + '/users'
        params = {"ident":tusr1,
                  "password":tusr1pw,
                  "fullname":"Test User One",
                  "loginType":3,
                  "email":tusr1 + "@fi.fi"
                }
        headers = {"Authorization": "fptoken " + token}
        try:
            resp = requests.post(url, timeout=5, params=params, headers=headers)
        except requests.exceptions.ConnectionError as e:
            fout("request exception: " + str(e))
            return None
            
        if resp.status_code != HTTP_CREATED:
            fout('unexpected status: {}'.format(resp.status_code))
            respError(resp)
            return None
        json = resp.json()
        print json
        userUrl = json['url']
    except Exception as e:
        print 'EXCEPTION in testCreateLocalUser: ', str(e) 
    return userUrl
    
# Test:
def restTest():
    try:
        testGetProjects()
        token = testGetToken()
        if token is None:
            fout('aborting - token is None')
            exit(0)
        testCreateLocalUser(token)
    except:
        tb = traceback.format_exc()
        fout(tb)


### Main: ################################################################################

def main(): 
#     if len(sys.argv) <= 1:
#         print 'Usage: {} <API_PREFIX>'.format(sys.argv[0])
#         exit(0)
#     AP = sys.argv[1]
#     USR = 'fpadmin'
#     PW = 'foo'
    restTest()

if __name__=="__main__":
   main()
   
##########################################################################################
