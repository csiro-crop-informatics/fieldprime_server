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


