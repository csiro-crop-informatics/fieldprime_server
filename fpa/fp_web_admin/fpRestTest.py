#!/usr/bin/python
#
#
#

import sys
import requests
import traceback
import json as modjson
import pprint
from const import *
#from fpRestApi import fprData

### Globals: #############################################################################

AP = 'http://0.0.0.0:5001/fpv1'
USR = 'fpadmin'
PW = 'foo'

tusr1 = 'testUser1'
tusr1pw = 'ohelfno33'
tusr1Name = 'Test User One'
tusr1Email = 'testUser1@some.where'
tproj1Name = 'testProject1'
ttrl1Name = 'testTrial1'
ttrl1Year = 2016
ttrl1Site = 'Canberra'

pp = pprint.PrettyPrinter(indent=4)

class RTException(Exception):
    pass

### Functions: ###########################################################################

def wout(msg):
    print '#### ', msg, ' =========================================================='
def fout(msg):
    print 'FAIL ', msg, ' =========================================================='
def nout(msg):
    print '  ', msg
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
        modjson.dumps(json)
        pp.pprint(json)

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
        return 'API error message:' + errmsg
    except Exception as e:
        return 'Cannot get error: ' + str(e)

def getUser(tokenHdr, url):
    try:
        resp = requests.get(url, timeout=5, headers=tokenHdr)
    except requests.exceptions.ConnectionError as e:
        fout("request exception in getUser: " + str(e))
        return None
    if resp.status_code != HTTP_OK:
        fout
    
# # Create local user:
# curl $AUTH -i -X POST -H "Content-Type: application/json" \
#      -d '{"ident":"testu1","password":"m","fullname":"Mutti Krupp","loginType":3,"email":"test@fi.fi"}' $FP/users
# 
# # Ideally here we would extract new user url from output, and use that subsequently.
def testLocalUser(tokenHdr):
    wout('Test create local user /projects?all=1')
    try:
        # First check if user already exists:
        try:
            url = AP+'/users/'+tusr1
            resp = requests.get(url, timeout=5, headers=tokenHdr)
        except requests.exceptions.ConnectionError as e:
            fout("request exception: " + str(e))
            return None
        if resp.status_code != HTTP_BAD_REQUEST:
            # user exists already. Delete her!
            nout("User {} already present. Deleting!".format(tusr1))
            resp = requests.delete(url, timeout=5, headers=tokenHdr)
            if resp.status_code != HTTP_OK:
                fout('Cannot delete user aborting test')
                return False
            nout('User deleted')
                
        # Create user:
        url = AP + '/users'
        params = {"ident":tusr1,
                  "password":tusr1pw,
                  "fullname":tusr1Name,
                  "loginType":3,
                  "email":tusr1Email
                }
        try:
            resp = requests.post(url, timeout=5, params=params, headers=tokenHdr)
        except requests.exceptions.ConnectionError as e:
            fout("request exception: " + str(e))
            return None            
        if resp.status_code != HTTP_CREATED:
            fout('unexpected status: {}\n  {}'.format(resp.status_code, respError(resp)))
            return None
        json = resp.json()
        userUrl = json['url']
        
        # Get created user and check values
        try:
            resp = requests.get(userUrl, timeout=5, headers=tokenHdr)
        except requests.exceptions.ConnectionError as e:
            fout("request exception: " + str(e))
            return None
        if resp.status_code != HTTP_OK:
            fout("Cannot GET created user {}".format(tusr1))
            return False
        juser = fprData(resp.json())
        pp.pprint(juser)
        if juser['email'] != tusr1Email:
            fout('email incorrect: {} should be {}'.format(juser['email'], tusr1Email))
        if juser['fullname'] != tusr1Name:
            fout('fullname incorrect: {} should be {}'.format(juser['fullname'], tusr1Name))
            
        # Update user:
                
    except Exception as e:
        fout('EXCEPTION in testCreateLocalUser: ' + str(e))
        fout(traceback.format_exc())
        return False
    return userUrl

def testCreateProject(tokenHdr, pname, cname, cemail, adminLogin):
    try:
        url = AP+'/projects'
        params = {
            'projectName': pname,
            'contactName': cname,
            'contactEmail': cemail,
            'ownDatabase': True,
            'adminLogin': adminLogin
        }
        resp = requests.post(url, timeout=5, data=params, headers=tokenHdr)
    except requests.exceptions.ConnectionError as e:
        raise RTException("request exception in testCreateProject: {}".format(str(e)))
    if resp.status_code != HTTP_CREATED:
        print resp
        raise RTException("unexpected status code: {}.\n  {}".format(
                                                resp.status_code, respError(resp)))
    return resp.json().get('url')

def testCreateTrial(tokenHdr, projUrl, name, year, site):
    try:
        url = AP+'/projects'
        params = {
            'projectName': pname,
            'contactName': cname,
            'contactEmail': cemail,
            'ownDatabase': True,
            'adminLogin': adminLogin
        }
        resp = requests.post(url, timeout=5, data=params, headers=tokenHdr)
    except requests.exceptions.ConnectionError as e:
        raise RTException("request exception in testCreateProject: {}".format(str(e)))
    if resp.status_code != HTTP_CREATED:
        print resp
        raise RTException("unexpected status code: {}.\n  {}".format(
                                                resp.status_code, respError(resp)))
    return resp.json().get('url')


def testGetUser():
    pass

# Test:
def restTest():
    try:
        testGetProjects()
        token = testGetToken()
        if token is None:
            fout('aborting - token is None')
            exit(0)
        tokenHdr = {"Authorization": "fptoken " + token}
        userUrl = testLocalUser(tokenHdr)
        if userUrl:
            nout('Created user: ' + userUrl)
            
        # Create project:
        wout('Test Create Project')        
        projUrl = testCreateProject(tokenHdr, tproj1Name, tusr1Name, tusr1Email, tusr1)
        nout("Created project: " + projUrl)
        
        # Get project:
        wout('Test Get Project')
        
        # Create trial:
        wout('Test Create Trial')
        trialUrl = testCreateTrial(tokenHdr, projUrl,
                                   name=ttrl1Name, year=ttrl1Year, site=ttrl1Site)
        
    except RTException as rte:
        fout("Aborting - " + str(rte))            
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
