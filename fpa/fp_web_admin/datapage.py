# datapage.py
# Michael Kirk 2013
#
# Some functions for displaying pages with a common bit (called
# Navigation Content here).
#

from flask import url_for, render_template, g
import fp_common.fpsys as fpsys
import fp_common.const as fpconst
import fpUtil as fpu
import forms


def selectorOfURLs(label, promptOptionString, listOfThings, thingValueFunc, thingNameFunc, selectedThingValue):
#-------------------------------------------------------------------------------
# Return html selector representing the items in listOfThings, the values are
# URLs (provided by function thingValueFunc) and selection of an item results
# in loading the associated URL. Presentation names are given by function thingNameFunc.
# If label is not None, the dropdown has this label.
# If promptOptionString is not None then a list item is added with this text
# (eg '..select thing..'). If selectedThingValue is not None then it should
# be one of the item values (URLs) and this will be preselected (in this case
# promptOptionString should be None).
#
    out = ''
    out += '<div style="overflow: hidden; display:inline-block;">'
    sel = '<div style="display:inline-block;min-width:200px">'
    sel += '<select class="form-control" style="min-width:300" name="tdd" id="tdd" ' + \
              'onchange="fplib.gotoLocationAndClearLastTab(this.options[this.selectedIndex].value);">'
    if promptOptionString is not None:
        sel +=     '<option value=0 selected="selected">{0}</option>'.format(promptOptionString)
    for thing in listOfThings:
        val = thingValueFunc(thing)
        sel += '<option value="{0}" {1}>{2}</option>'.format(
            val,
            'selected="selected"' if val ==  selectedThingValue else '',
            thingNameFunc(thing))
    sel +=     '</select>'
    sel +=   '</div>'

    if label is not None:
        out += fpu.htmlLabelValue(label, sel)
    else:
        out = sel

    out += '</div>'
    return out

def formElements4LocalUserSelfManagement():
# User details form:
    return [
        forms.formElement('User Name', 'Full name of new user', 'fullname', 'xcontId',
                          etype=forms.formElement.TEXT, typeSpecificData=g.user.getName()),
        forms.formElement('User Email', 'Email address of new user', 'email', 'xemailId',
                          etype=forms.formElement.TEXT, typeSpecificData=g.user.getEmail()),
        forms.formElement('Current Password', '', 'oldPassword', 'xoldPassword',
                          etype=forms.formElement.PASSWORD),
        forms.formElement('New Password', 'enter new password', 'password', 'xfpcuPassword1',
                          etype=forms.formElement.PASSWORD),
    ]

def userBit():
#-----------------------------------------------------------------------------------------
# 
    user = g.user
    ident = user.getIdent()
    modalStuff = forms.makeModalForm(
               'User Profile', formElements4LocalUserSelfManagement(),
               divId='updateUserForm',
               submitUrl=url_for('webRest.urlUpdateUser', ident=ident, _external=True), method="PUT",
               show=None)
    out = ''
    if user.getLoginType() == fpconst.LOGIN_TYPE_LOCAL:
        out += modalStuff # modal form stuff needed if user name a link
        userNameLink = '<a href="#" data-toggle="modal" data-target="#updateUserForm">{}</a>'.format(ident)
    else:
        userNameLink = ident
    out  += '<span>' + fpu.htmlLabelValue('User', userNameLink) + '</span>'
    out += '<a href="{0}" class="btn btn-primary" role="button">Sign Out</a>'.format(url_for('urlLogout'))
    return out


def _dataNavigationContent(trialId):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
# trialId is only relevant if sess has a current project. If so then..
# If trialId is >=0:
#     The trial select dropdown is shown with the specified trial selected.
# If trialId is None:
#     The trial select dropdown is shown with no trial selected.
# If trialId < 0:
#     The trial select dropdown is not shown.
#
    userIdent = g.user.getIdent()
    projectName = None if g.userProject is None else g.userProject.getProjectName()
    projId = None if g.userProject is None else g.userProject.getProjectId()

    nc = ''
    #---------------------------------------------------------------------------
    # First row. User and user specific buttons:
    #
    # show current user:
    r1c1  = userBit()

    # Show non project specific buttons:
    r1c2 = '<div style="float:right">'
    if fpsys.User.sHasPermission(userIdent, fpsys.User.PERMISSION_OMNIPOTENCE):
        r1c2 += '<a href="{0}"><span class="fa fa-user"></span>Manage FP</a>'.format(url_for('urlFPAdmin'))
    r1c2 +=   '<a href="{0}"><span class="fa fa-download"></span> Download App</a>'.format(url_for("downloadApp"))
    r1c2 +=   '<a style="white-space:nowrap" href="https://docs.google.com/document/d/1SpKO_lPj0YzhMV6RKlzPgpNDGFhpaF-kCu1-NTmgZmc/pub">' + \
            '<span class="fa fa-question-circle"></span> App User Guide</a>'
    r1c2 += '</div>'
    nc += fpu.bsRow(fpu.bsCol(r1c1, numCols=6) + fpu.bsCol(r1c2, numCols=6))

    #---------------------------------------------------------------------------
    # Second row. Project and project specific buttons:

    # Make select of user's projects.
    # Note we need to construct the URL for retrieving the project page in javascript,
    # and hence cannot use url_for.
    projList, errMsg = fpsys.getUserProjects(userIdent)
    if errMsg:
        return 'A problem occurred in finding projects for user {0}:{1}'.format(userIdent, errMsg)
    if not projList:
        return nc
        return 'A problem occurred in finding projects for user {0}:{1}'.format(userIdent, errMsg)
    r2c1 = selectorOfURLs('Project', '..Select Project..' if projectName is None else None, projList,
        lambda p: url_for('urlProject', projId=p.getProjectId()),
        lambda p: p.projectName(),
        None if projectName is None else url_for('urlProject', projId=projId))

    r2 = fpu.bsCol(r2c1, numCols=6)

    # Show project specific buttons:
    if projectName is not None:
        r2c2 = '<div style="float:right; display:inline-block">'
        if g.userProject.hasAdminRights():
            r2c2 += '<a href="{0}"><span class="fa fa-user"></span> Administration</a>'.format(url_for('urlUserDetails', projectName=projectName))
        r2c2 += '<a href="{0}"><span class="fa fa-gear"></span> System Traits</a>'.format(url_for('urlSystemTraits', projectName=projectName))
        r2c2 += '<a href="{0}"><span class="fa fa-magic"></span> Create New Trial</a>'.format(url_for('urlNewTrial', projId=projId))
        r2c2 += '</div><div style="clear:both"></div>'
        r2 += fpu.bsCol(r2c2, numCols=6, extra='style="white-space:nowrap"')

    nc += fpu.bsRow(r2)

    #---------------------------------------------------------------------------
    # Trial selector:
    if projectName is not None:
        # Add trial selector:
        if trialId is None or trialId >= 0:
            r3c1 = selectorOfURLs('Trial', '..Select Trial..' if trialId is None else None,
                g.userProject.getModelProject().getTrials(),
                lambda t: url_for('urlTrial', projId=projId, trialId=t.id), lambda t: t.name,
                None if trialId is None else url_for('urlTrial', projId=projId, trialId=trialId))
            nc += fpu.bsRow(fpu.bsCol(r3c1, numCols=6))

    nc += fpu.htmlHorizontalRule()
    return nc


def dataPage(title, content, trialId=None):
#----------------------------------------------------------------------------
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
# See comment on _dataNavigationContent for trialId semantics.
#
    nc = _dataNavigationContent(trialId)
    return render_template('dataPage.html', navContent=nc, content=content, title=title)

def dataPageTest(sess, title, content, trialId=None):
#----------------------------------------------------------------------------
# Test version: copy datapage.html to dataPageTest.html, and base.html to baseTest.html
# and hack away.
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
# See comment on _dataNavigationContent for trialId semantics.
#
    nc = _dataNavigationContent(trialId)
    return render_template('dataPageTest.html', navContent=nc, content=content, title=title)

def dataTemplatePage(sess, template, **kwargs):
#----------------------------------------------------------------------------
# Return page for user data with given template, kwargs are passed through
# to the template. The point of this function is to add the navigation content.
# NB, if trialId is not specified in kwargs, then no trial dropdown is shown.
#
    if 'trialId' in kwargs:
        nc = _dataNavigationContent(trialId=kwargs['trialId'])
    else:
        nc = _dataNavigationContent(trialId=-1)
    return render_template(template, navContent=nc, **kwargs)


def dataErrorPage(sess, errMsg, trialId=None):
#----------------------------------------------------------------------------
# Show error message in user data page.
    return dataPage(content=errMsg, title='Error', trialId=trialId)

