#!/usr/bin/python
#
#
#

import sys
import getopt
import requests
import traceback
import json as modjson
import pprint
import base64

from const import *

### Globals: #############################################################################

AP = 'http://0.0.0.0:5001/fpv1'
USR = 'fpadmin'
PW = 'foo'

gClear = False    # Should we clear db of previous objects with the names used in this test.

# Test object names, attributes..
tusr1 = 'testUser1'
tusr1pw = 'ohelfno33'
tusr1Name = 'Test User One'
tusr1Email = 'testUser1@some.where'
tusr2 = 'testUser2'
tusr2pw = 'oFluffinHippo'
tusr1Name = 'Test User Two'
tusr1Email = 'testUser2@some.where'
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
def jout(json):
    pp.pprint(json)

def fprData(jsonResponse):
    return jsonResponse["data"]

def respError(resp):
# Print error message from api resp, if available.
    try:
        json = resp.json()
        errmsg = json['error']
        return 'API error message:' + errmsg
    except Exception as e:
        return 'Cannot get error: ' + str(e)

def makeBasicAuthenticationHeader(user, password):
    usrPass = "{}:{}".format(user, password)
    b64Val = base64.b64encode(usrPass)
    header = {"Authorization": 'Basic ' + b64Val}
    return header

   
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

def getProjects():
    try:
        # Get Projects using basic authentication
        url = AP + '/projects'
        params = {"all":1}
        try:
            resp = requests.get(url, timeout=5, params=params, auth=(USR, PW))
        except requests.exceptions.ConnectionError as e:
            raise RTException("requests exception in tgetProjects: {}".format(str(e)))           
        if resp.status_code != HTTP_OK:
            raise RTException('unexpected status: {}'.format(resp.status_code))
        json = resp.json()
        data = json['data']
        return data
    except RTException:
        raise
    except Exception as e:
        print 'EXCEPTION in getProjects: ', str(e) 

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
        
def testGetToken(usr, pw):
    wout('Test get /token')  
    try:
        url = AP + '/token'
        resp = requests.get(url, timeout=5, auth=(usr, pw))
    except Exception, e:
        print 'getToken error: ' + str(e)
        return None
    if resp.status_code != HTTP_OK:
        fout('unexpected status: {}'.format(resp.status_code))
        return
    json = resp.json()
    return fprData(json)["token"]

def getUser(tokenHdr, url):
    try:
        resp = requests.get(url, timeout=5, headers=tokenHdr)
    except requests.exceptions.ConnectionError as e:
        fout("request exception in getUser: " + str(e))
        return None
    if resp.status_code != HTTP_OK:
        fout
    
def testLocalUser(tokenHdr):
    wout('Test create local user /projects?all=1')
    try:
        if gClear:
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

def deleteProject(tokenHdr, url):
    resp = requests.delete(url, timeout=5, headers=tokenHdr)
    if resp.status_code != HTTP_OK:
        raise RTException("unexpected status code in deleteProject: {}".format(resp.status_code))
        
def testCreateProject(tokenHdr, pname, cname, cemail, adminLogin):
    if gClear:
        projects = getProjects()
        for proj in projects:
            if proj['projectName'] == pname:
                nout('project {} already exists - deleting it'.format(pname))
                deleteProject(tokenHdr, proj['url'])
        
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
#   trialName : name project - must be appropriate.
#   trialYear : text
#   trialSite : text
#   trialAcronym : text
#   nodeCreation : 'true' or 'false'
#   rowAlias : text
#   colAlias : text
    try:
        params = {
            'trialName': name,
            'trialYear': year,
            'trialSite': site
        }
        resp = requests.post(projUrl, timeout=5, data=params, headers=tokenHdr)
    except requests.exceptions.ConnectionError as e:
        raise RTException("request exception in testCreateProject: {}".format(str(e)))
    if resp.status_code != HTTP_CREATED:
        print resp
        raise RTException("unexpected status code: {}.\n  {}".format(
                                                resp.status_code, respError(resp)))
    return resp.json().get('url')


def testGetUser():
    pass

def getProject(authHdr, projUrl):
    print 'in getProject'
    try:
        resp = requests.get(projUrl, timeout=5, headers=authHdr)
    except requests.exceptions.ConnectionError as e:
        raise RTException("request exception in getProject: {}".format(str(e)))
    if resp.status_code != HTTP_OK:
        raise RTException("unexpected status code: {}.\n  {}".format(
                                                resp.status_code, respError(resp)))
    return fprData(resp.json())
  
# Test:
def restTest():
    try:
        # Get Projects - without token:
        testGetProjects()
        
        token = testGetToken(USR, PW)
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
        basicAuthHdr = makeBasicAuthenticationHeader(tusr1, tusr1pw)
        proj = getProject(basicAuthHdr, projUrl)
        if proj.get('projectName') != tproj1Name:
            fout('Incorrect project name in get: expected {}, got {}'.format(tproj1Name, proj.get('projectName')))
            return
        nout("OK: Got project:")
        jout(proj)
        
        # Create trial:
        wout('Test Create Trial')
        createTrialUrl = proj['trialUrl']
        trialUrl = testCreateTrial(basicAuthHdr, createTrialUrl,
                                   name=ttrl1Name, year=ttrl1Year, site=ttrl1Site)
        
        # Update trial:
        
        # Delete trial:
          
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

    global gClear
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ch")
    except getopt.GetoptError:
        print 'Problem with command line arguments'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-c':
            gClear = True
        if opt == '-h':
            print 'Usage: {} [-c] [-h]'.format(sys.argv[0])
            print '  -h : show this help'
            print '  -c : clear objects from the db with names the same as used in these tests'
            exit(0)
    restTest()

if __name__=="__main__":
   main()
   
##########################################################################################
