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


def HtmlForm(content, id=None, post=False, onsubmit='', multipart=False):
#-----------------------------------------------------------------------
# Returns the content surrounded by html form tags.
# NB content can be either a string, or a function returning one.
#
    contentPart = content if isinstance(content, str) else content()
    enctypePart = "enctype='multipart/form-data'" if multipart else ""
    methodPart = "method='{0}'".format('POST' if post else 'GET')
    submitPart = ' onsubmit="{0}"'.format(onsubmit) if onsubmit else ''
    idPart = ' id="{0}"'.format(id) if id is not None else ''
    return "<form {0} {1} {2} {3}>\n{4}</form>".format(methodPart, submitPart, enctypePart, idPart, contentPart)


def HtmlFieldset(content, legend=None):
#-----------------------------------------------------------------------
# Returns html for a fieldset, with the given content and legend.
# NB content can be either a string, or a function returning one.
#
    cont = content if isinstance(content, str) else content()
    leg = '<legend><h3>{0}</h3></legend>'.format(legend) if legend is not None else ''
    return '<fieldset>{0}{1}</fieldset>'.format(leg, cont)

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
