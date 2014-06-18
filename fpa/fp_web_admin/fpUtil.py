# fpUtil.py
# Michael Kirk 2013
# Utility code for fprime
#
#

import sys
import time
import dbUtil

#-----------------------------------------------------------------------


def GetString(x):
#-----------------------------------------------------------------------
# For when x is a string, or a function returning string
#
    if isinstance(x, str): return x
    return x()


def HtmlForm(content, post=False, onsubmit=''):
#-----------------------------------------------------------------------
# Returns the content surrounded by html form tags.
# NB content can be either a string, or a function returning one.
#
    c = content if isinstance(content, str) else content()
    submitItem = ' onsubmit="{0}"'.format(onsubmit) if onsubmit else ''
    return "<form method='{0}'{1}>".format('POST' if post else 'GET', submitItem) + c + "</form>"


def HtmlFieldset(content, legend):
#-----------------------------------------------------------------------
# Returns html for a fieldset, with the given content and legend.
# NB content can be either a string, or a function returning one.
#
    c = content if isinstance(content, str) else content()
    return "<fieldset><legend><h3>" + legend + "</h3></legend>" + c + "</fieldset>"

def htmlHeaderFieldset(content, legend):
#-----------------------------------------------------------------------
# Returns html to show legend as a header2 and then the content in a fieldset.
#
    return "<h2>{0}</h2><fieldset>{1}</fieldset>".format(legend, content)


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


def HtmlButtonLink2(label, click):
#-----------------------------------------------------------------------
# This version has the button inside a form, sometimes (eg when within
# a table cell), this seems to be necessary.
    return "<form><input type=button style=\"color:red\" onclick=\"window.location.href='{0}'\" value='{1}' /></form>".format(click, label)
