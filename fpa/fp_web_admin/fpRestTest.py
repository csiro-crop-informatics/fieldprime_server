#!/usr/bin/python
#
# fpRestTest.py
# Michael Kirk 2016
# 
# Test script, and tools, for testing the FieldPrime REST API.
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
PW = 'food'

gClear = False    # Should we clear db of previous objects with the names used in this test.

# Test object names, attributes..
tusr1 = 'testUser1'
tusr1pw = 'ohelfno33'
tusr1Name = 'Test User One'
tusr1Email = 'testUser1@some.where'
tusr2 = 'testUser2'
tusr2pw = 'oFluffinHippo'
tusr2Name = 'Test User Two'
tusr2Email = 'testUser2@some.where'
tproj1Name = 'testProject1'
ttrl1Name = 'testTrial1'
ttrl1Year = 2016
ttrl1Site = 'Canberra'

pp = pprint.PrettyPrinter(indent=4)

class RTException(Exception):
    pass

### Functions: ###########################################################################

### Utility funcs: #######################################################################

def hout(msg): # header out - indicate start of test
    print '#### ', msg, ' =========================================================='
def fout(msg=''): # fail out - failed test
    print 'FAIL ', msg, ' =========================================================='
def sout(msg=''): # success out - passed test
    print '  PASS: ', msg
def nout(msg): # normal out - informational text
    print '    ', msg
def jout(json): # json out - pretty print json
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

def getSomething(authHdr, url, somethingName='something', params=None):
# Makes get request on url. If HTTP_OK received returns the
# json response object. Raise exception if not OK or connection error occurs.
#
    try:
        resp = requests.get(url, timeout=5, headers=authHdr, params=params)
    except requests.exceptions.ConnectionError as e:
        raise RTException("requests exception getting {}: {}".format(somethingName, str(e)))
    if resp.status_code != HTTP_OK:
        raise RTException("unexpected status code ({}) getting {}.\n  {}".format(
            resp.status_code, somethingName, respError(resp)))
    return resp.json()

def createSomething(authHdr, url, somethingName='something', params=None):
# Makes get request on url. If HTTP_OK received returns the
# json response object. Raise exception if not OK or connection error occurs.
    try:
        resp = requests.post(url, timeout=5, headers=authHdr, json=params)
    except requests.exceptions.ConnectionError as e:
        raise RTException("requests exception creating {}: {}".format(somethingName, str(e)))
    if resp.status_code != HTTP_CREATED:
        raise RTException("unexpected status code ({}) getting {}.\n  {}".format(
            resp.status_code, somethingName, respError(resp)))
    return resp.json()

def deleteSomething(authHdr, url, somethingName='something'):
# Makes delete request on url. 
# Raises exception if not HTTP_OK or connection error occurs.
    try:
        resp = requests.delete(url, timeout=5, headers=authHdr)
    except requests.exceptions.ConnectionError as e:
        raise RTException("requests exception deleting {}: {}".format(somethingName, str(e)))
    if resp.status_code != HTTP_OK:
        raise RTException("unexpected status code ({}) deleting {}.\n  {}".format(
            resp.status_code, somethingName, respError(resp)))        

def checkIsSame(thisThing, shouldBeThis, thingName='value'):
# Raises exception if not thisThing equals shouldBeThis
    if str(thisThing) != str(shouldBeThis):
        raise RTException('Incorrect {}: expected {}, got {}'.format(thingName, shouldBeThis, thisThing))

### Test funcs: ##########################################################################

def testGetProjects(authHdr):
    try:
        hout('Test get /projects?all=1')     
        json = getSomething(authHdr, AP + '/projects',
                                somethingName='project', params={'all':1})
        data = fprData(json)
        nout('{} projects found'.format(len(data)))
        modjson.dumps(json)
        jout(json)
    except RTException:
        raise                
    except Exception as e:
        raise RTException('EXCEPTION in testGetProjects: {}'.format(str(e))) 
        
def testGetToken(authHdr):
    hout('Test get /token')
    token = fprData(getSomething(authHdr, AP + '/token', somethingName='token')).get('token')
    if token is None:
        raise RTException('token is None')
    sout('Got token: ' + token)
    return token

def deleteUserNoFuss(authHdr, userId):
# Try delete user, ignore errors as user may not exist
    url = AP+'/users/'+userId
    try:
        deleteSomething(authHdr, url)
    except RTException as e:
        pass
    

def testLocalUser(authHdr):
    hout('Test create local user /projects?all=1')
    try:
        if gClear:
            # First check if user already exists:
            try:
                url = AP+'/users/'+tusr1
                resp = requests.get(url, timeout=5, headers=authHdr)
            except requests.exceptions.ConnectionError as e:
                fout("request exception: " + str(e))
                return None
            if resp.status_code != HTTP_BAD_REQUEST:
                # user exists already. Delete her!
                nout("User {} already present. Deleting!".format(tusr1))
                resp = requests.delete(url, timeout=5, headers=authHdr)
                if resp.status_code != HTTP_OK:
                    fout('Cannot delete user aborting test')
                    return False
                sout('User deleted')
                
        # Create user:
        json = createSomething(authHdr, AP + '/users', somethingName='user', params = {
                  "ident":tusr1,
                  "password":tusr1pw,
                  "fullname":tusr1Name,
                  "loginType":3,
                  "email":tusr1Email
                })
        userUrl = json['url']
        
        # Get created user and check values:
        juser = fprData(getSomething(authHdr, userUrl, somethingName='user'))
        jout(juser)
        checkIsSame(juser['email'], tusr1Email, 'user email')
        checkIsSame(juser['fullname'], tusr1Name, 'user fullname')
            
        # Update user: todo
        
    except RTException:
        raise                
    except Exception as e:
        fout('EXCEPTION in testCreateLocalUser: ' + str(e))
        fout(traceback.format_exc())
        raise RTException('EXCEPTION in testLocalUser: {}'.format(str(e))) 
    return userUrl

def testCreateProject(authHdr, pname, cname, cemail, adminLogin):
    if gClear:
        projects = fprData(getSomething(authHdr, AP + '/projects',
                                        somethingName='project', params={'all':1}))
        for proj in projects:
            if proj['projectName'] == pname:
                nout('project {} already exists - deleting it'.format(pname))
                deleteSomething(authHdr, proj['url'], "project")
    # create project:           
    resp = createSomething(authHdr, AP+'/projects', somethingName='projects', params={
            'projectName': pname,
            'contactName': cname,
            'contactEmail': cemail,
            'ownDatabase': True,
            'adminLogin': adminLogin
        })
    return resp.get('url')

def testCreateTrial(authHdr, projUrl, name, year, site):
    resp = createSomething(authHdr, projUrl, somethingName='trial', params= {
            'trialName': name,
            'trialYear': year,
            'trialSite': site,
            'attributes': [{'name':'att1', 'datatype':'integer'},
                           {'name':'att2', 'datatype':'decimal'},
                           {'name':'att3'}],
            'nodes':[
                {'index1':1, 'index2':1, 'attvals':{'att1':1, 'att2':1.2, 'att3':'hello'}},
                {'index1':1, 'index2':2, 'attvals':{'att1':2, 'att2':1.3, 'att3':'world'}},
                {'index1':1, 'index2':3, 'attvals':{'att3':'goodbye'}},
            ]
        })
    return resp.get('url')

def testProjectUserStuff(adminAuthHdr, user1AuthHdr, projUsersUrl):
        # Add user to project:
        hout('Add project user')
        if gClear: deleteUserNoFuss(adminAuthHdr, tusr2)
        createSomething(adminAuthHdr, AP + '/users', somethingName='user', params = {
                  "ident":tusr2,
                  "password":tusr2pw,
                  "fullname":tusr2Name,
                  "loginType":3,
                  "email":tusr2Email
                })
        resp = createSomething(user1AuthHdr, projUsersUrl, somethingName='user',
            params = {
            'ident': tusr2,
            'admin': False
            })
        sout()
        
        # Get project users:
        hout('Get project users')
        nout('url: ' + projUsersUrl)
        data = fprData(getSomething(user1AuthHdr, projUsersUrl, somethingName='projectUser'))
        jout(data)
        # We should have 2 users, tusr1 (admin) and tusr2 (not admin):
        userPerms = {}
        for x in data: userPerms[x['ident']] = x['admin']
        if len(data) != 2: fout('Expected 2 users in project, but got {}'.format(len(data)))
        checkIsSame(userPerms[tusr1], True, thingName='admin rights')
        checkIsSame(userPerms[tusr2], False, thingName='admin rights')
        sout()

 
def testProjectTrialStuff(authHdr, projTrialsUrl):
    # Create trial:
    hout('Test Create Trial')
    trialUrl = testCreateTrial(authHdr, projTrialsUrl,
                               name=ttrl1Name, year=ttrl1Year, site=ttrl1Site)
    sout("Trial Created: " + trialUrl)
    
    # Get specific trial:
    hout('Test get trials')
    trial = fprData(getSomething(authHdr, trialUrl, "trial"))
    checkIsSame(trial.get('name'), ttrl1Name, 'trial name')
    checkIsSame(trial.get('year'), ttrl1Year, 'trial year')
    checkIsSame(trial.get('site'), ttrl1Site, 'trial site')
    jout(trial)
    sout("Got trial from URL")

    # Get trials:
    hout('Get project trial list')
    trialList = fprData(getSomething(authHdr, projTrialsUrl, "trial list"))
    if len(trialList) != 1:
        raise RTException("Trial list wrong length of {}, should be 1".format(len(trialList)))
    if trialList[0] != trialUrl:
        raise RTException("Trial url wrong. Got{}, expected {}".format(trialList[0], trialUrl))
    jout(trialList)
    sout('project trial list')
    
    # Update trial:
    
    # Delete trial:
#     hout('Delete trial')
#     deleteSomething(authHdr, trialUrl, 'trial')
#     sout()
    
# Test:
def restTest():
    try:
        adminAuthHdr = makeBasicAuthenticationHeader(USR, PW)

        # Get Projects - with admin basic auth:
        testGetProjects(adminAuthHdr)
        
        token = testGetToken(adminAuthHdr)
        tokenHdr = {"Authorization": "fptoken " + token}
        userUrl = testLocalUser(tokenHdr)
        sout('Created user: ' + userUrl)
            
        # Create project:
        hout('Test Create Project')        
        projUrl = testCreateProject(tokenHdr, tproj1Name, tusr1Name, tusr1Email, tusr1)
        sout("Created project: " + projUrl)
        
        # Get project:
        hout('Test Get Project')
        user1AuthHdr = makeBasicAuthenticationHeader(tusr1, tusr1pw)
        proj = fprData(getSomething(user1AuthHdr, projUrl, somethingName='project'))
        checkIsSame(proj.get('projectName'), tproj1Name, 'project name')
        sout("Got project:")
        jout(proj)
        
        # Test project user functionality:
        testProjectUserStuff(adminAuthHdr, user1AuthHdr, proj.get('urlUsers'))
        
        # Test project trial functionality:
        testProjectTrialStuff(user1AuthHdr, proj.get('urlTrials'))
        
        # todo - test trial stuff as super user without specific project access
        
        hout('Finished all tests')
    except RTException as rte:
        fout("ABORTING - " + str(rte))            
        fout(traceback.format_exc())
    except Exception as e:
        fout("ABORTING unexpected exception - " + str(e))            
        fout(traceback.format_exc())


### Main: ################################################################################

def main(): 
#     if len(sys.argv) <= 1:
#         print 'Usage: {} <API_PREFIX>'.format(sys.argv[0])
#         exit(0)
# todo: Probably should just clear everything at the beginning if clear is specified.
# Also incremental option might be useful, i.e. don't clear and skip tests already
# passed (as detected by inspection?). Or command line flags to do specific tests (but
# note dependence of some test on results of previous ones that created things).
# A makefile might be a way to go..
#
    def usage():
        print 'Usage: {} [-c] [-h]'.format(sys.argv[0])
        print '  -h : show this help'
        print '  -c : clear objects from the db with names the same as used in these tests'
        exit(0)
        
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
            usage()
    restTest()

if __name__=="__main__":
   main()
   
##########################################################################################
