# fpUtil.py
# Michael Kirk 2013
# Utility code for fprime
#
#

import sys
import session
import time
import dbUtil


__all__ = ['footer', 'header', 'GetFormKey', 'LoginForm',
           'ShowHtml', 'LOGIN_TIMEOUT', 'HOMEPAGE', 'HtmlForm',
           'HtmlFieldset', 'FrontPage']

#-----------------------------------------------------------------------

gTraitTypes = {"Integer":0, "Decimal":1, "String":2, "Categorical":3, "Date":4}

HOMEPAGE = "/fieldprime"
LOGIN_TIMEOUT = 300


#-----------------------------------------------------------------------


def GetString(x):
#-----------------------------------------------------------------------
# For when x is a string, or a function returning string
#
    if isinstance(x, str): return x
    return x()


def header(title):
#-----------------------------------------------------------------------
    print "Content-type: text/html\n"
    jscriptURL = "/fp/fp.js"
    print "<HTML><HEAD><script src='{1}'></script><TITLE>{0}</TITLE>\n</HEAD>\n<BODY>\n".format(title, jscriptURL)
    print "<h1>Field Prime Server Management</h1>"
    print "<a href='{0}'>Home</a>".format(HOMEPAGE)
    print HtmlButtonLink("Login as Different User", "{0}?op=login".format(HOMEPAGE))
    print "<hr>"


def footer():
#-----------------------------------------------------------------------
    print "<hr>"
    print "<a href=\"mailto:***REMOVED***?subject=Field Prime Management Server\">Contact Webmaster</a>"
    print "</BODY></HTML>"


def GetFormKey(form, key):
#-----------------------------------------------------------------------
    if form.has_key(key) and len(key) > 0:
        return form[key].value
    return False


def HtmlForm(content):
#-----------------------------------------------------------------------
# Returns the content surrounded by html form tags.
# NB content can be either a string, or a function returning one.
#
    c = content if isinstance(content, str) else content()
    return "<form>" + c + "</form>"


def HtmlFieldset(content, legend):
#-----------------------------------------------------------------------
# Returns html for a fieldset, with the given content and legend.
# NB content can be either a string, or a function returning one.
#
    c = content if isinstance(content, str) else content()
    return "<fieldset><legend><h3>" + legend + "</h3></legend>" + c + "</fieldset>"


def ShowHtml(sess, title, content):
#-------------------------------------------------------------------------------------------
# Show a page with the given title and content (should not include header/footer) and exit.
# NB - Exits.
#
    header(title)
    print GetString(content)
    footer()
    Exit(sess)


def LoginForm(sess, msg = ''):
#-----------------------------------------------------------------------
# NB - Exits script.
#
#
    ShowHtml(sess, "Field Prime Login", """
<CENTER>
<FORM method="POST" action="{0}">
<paragraph> Enter your login name: <input type="text" name="login">
<paragraph> Enter your password: <input type=password name="password">
<paragraph> <input type="submit" value="Connect">
</FORM>
</CENTER>
</form>
{1}
""".format(HOMEPAGE, msg))


def Exit(sess=None):
#-----------------------------------------------------------------------
# Exits script, after closing sess if present
#
    if sess:
        sess.close()
    sys.exit()

def HtmlButtonLink(label, click):
#-----------------------------------------------------------------------
    return "<button style=\"color: red\" onClick=\"window.location='{0}'\">{1}</button>".format(click, label)


def FrontPage(sess):
#-----------------------------------------------------------------------
# Shows the main page after login (then exits)
#
#-----------------------------------------------------------------------
    x = sess.timeSinceUse()
    sess.resetLastUseTime()
    suser = sess.GetUser()
    header("Last visit found: " + (suser if suser else "no-one"))
    print "hallo <a href={0}?op=user>{1}</a> last seen {2} <br>".format(HOMEPAGE, suser, time.asctime(time.gmtime(sess.getLastUseTime())))
    print "Time since last seen: {0} <br>".format(x)
    print "Time till login expires: {0} <br><p>".format(LOGIN_TIMEOUT - x)

    # Administer passwords button:
    print "<p>" + HtmlButtonLink("Administer Passwords", "{0}?op=user".format(HOMEPAGE))

    # Traits:
    trials = dbUtil.GetTrials(sess)
    trialListHtml = "No trials yet" if len(trials) < 1 else ""
    for t in trials:
        trialListHtml += "<li><a href={0}?op=showTrial&tid={1}>{2}</a></li>".format(HOMEPAGE, t.id, t.name)

    print HtmlFieldset(HtmlForm(trialListHtml) +  HtmlButtonLink("Create New Trial", HOMEPAGE + "?op=newTrial"), "Current Trials")

    # System Traits:
    sysTraits = dbUtil.GetSysTraits(sess)
    from fpTrait import TraitListHtmlTable
    sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else TraitListHtmlTable(sysTraits)
    print HtmlFieldset(HtmlForm(sysTraitListHtml) + HtmlButtonLink("Create New System Trait", HOMEPAGE + "?op=newTrait&tid=sys"), "System Traits")

    # End of page:
    footer()
    Exit(sess)
