# datapage.py
# Michael Kirk 2013
#
# Some functions for displaying pages with a common bit (called
# Navigation Content here).
#

from flask import Flask, request, Response, redirect, url_for, render_template, g, make_response
import fpsys
from dbUtil import GetTrials
from const import *

def dataNavigationContent(sess, trialId):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
    ### User and user specific buttons:

    # Show current user:
    nc = "<h1 style='float:left; padding-right:20px; margin:0'>User: {0}</h1>".format(sess.getUser())

    # Show non project specific buttons:
    nc += '<div style="float:right; margin-top:10px">'
    nc += '<a href="{0}"><span class="fa fa-download"></span> Download App</a>'.format(url_for("downloadApp"))
    nc += '<a href="https://docs.google.com/document/d/1SpKO_lPj0YzhMV6RKlzPgpNDGFhpaF-kCu1-NTmgZmc/pub"><span class="fa fa-question-circle"></span> App User Guide</a>'
    nc += '</div><div style="clear:both"></div>'

    ### Project and project specific buttons:

    # There are currently 2 types of login, ***REMOVED***, and the project login.
    # ***REMOVED*** users may have access rights to multiple project so they get
    # a dropdown project selection. Project logins have access to a single
    # project only, so they don't get a drop down. Set projectSelectorHtml
    # accordingly:
    if sess.getLoginType() == LOGIN_TYPE_***REMOVED***:
        # Make select of user's projects.
        # Note we need to construct the URL for retrieving the project page in javascript,
        # and hence cannot use url_for.
        projList, errMsg = fpsys.getProjects(sess.getUser())
        if errMsg or not projList:
            return 'A problem occurred in finding projects for user {0}:{1}'.format(sess.getUser(), errMsg)

        # MFK do we really want a form here?
        hackedProjUrl = url_for('urlProject', project='')[:-1]
        projectSelectorHtml = '''
        <script>
        function submitProjSelection(frm) {{
            var e = document.getElementById("project");
            var proj = e.options[e.selectedIndex].value;
            frm.action = "{0}" + proj
            frm.submit()
        }}
        </script>
        <form  method="GET" style='display:inline;'>
        <select name="project" id="project" onchange="submitProjSelection(this.form)">'''.format(hackedProjUrl)
        for proj in projList:
            projectSelectorHtml += '<option value="{0}" {1}><h1>{0}</h1></option>'.format(
                    proj, 'selected="selected"' if proj == sess.getProjectName() else '')
        projectSelectorHtml += '</select></form>'
    else:
        projectSelectorHtml = sess.getProjectName()

    # Show current project:
    nc += "<h1 style='float:left; padding-right:20px; margin:0'>Project:{0}</h1>".format(projectSelectorHtml)

    # Show non project specific buttons:
    nc += '<div style="float:right; margin-top:10px">'
    if sess.adminRights():
        nc += '<a href="{0}"><span class="fa fa-user"></span> Administration</a>'.format(url_for('urlUserDetails', projectName=sess.getProjectName()))
    nc += '<a href="{0}"><span class="fa fa-gear"></span> System Traits</a>'.format(url_for('urlSystemTraits', projectName=sess.getProjectName()))
    nc += '<a href="{0}"><span class="fa fa-magic"></span> Create New Trial</a>'.format(url_for("newTrial"))
    nc += '</div><div style="clear:both"></div>'


    trials = GetTrials(sess)
    trialListHtml = None if len(trials) < 1 else ""
    for t in trials:
        if "{}".format(t.id) == "{}".format(trialId):
            trialListHtml += "\n  <li class='fa-li fa selected'><a href={0}>{1}</a></li>".format(url_for("urlTrial", trialId=t.id), t.name)
        else:
            trialListHtml += "\n  <li class='fa-li fa'><a href={0}>{1}</a></li>".format(url_for("urlTrial", trialId=t.id), t.name)

    if trialListHtml:
        nc += '<hr style="margin:15px 0; border: 1px solid #aaa;">'
        nc += "<h2>Trials:</h2><ul class='fa-ul'>"
        nc += trialListHtml
        nc += '</ul><hr style="margin:15px 0; border: 1px solid #aaa;">'
    return nc



def dataPage(sess, title, content, trialId=None):
#----------------------------------------------------------------------------
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
#
    nc = dataNavigationContent(sess, trialId)
    return render_template('dataPage.html', navContent=nc, content=content, title=title)

def dataTemplatePage(sess, template, **kwargs):
#----------------------------------------------------------------------------
# Return page for user data with given template, kwargs are passed through
# to the template. The point of this function is to add the navigation content.
#
    if 'trialId' in kwargs:
        nc = dataNavigationContent(sess, trialId=kwargs['trialId'])
    else:
        nc = dataNavigationContent(sess, trialId="-1")
    # nc = dataNavigationContent(sess) # Generate content for navigation bar:
    return render_template(template, navContent=nc, **kwargs)

def dataErrorPage(sess, errMsg):
#----------------------------------------------------------------------------
# Show error message in user data page.
    return dataPage(sess, content=errMsg, title='Error')
