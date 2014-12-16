# fpUtil.py
# Michael Kirk 2013,2014
# Utility code for FieldPrime web admin.
#
#

import sys
import time
import dbUtil
from flask import url_for

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
    return "<input type='button' onclick=\"window.location.href='{0}'\" value='{1}' />".format(click, label)
    #return "<form><input type=button style=\"color:red\" onclick=\"window.location.href='{0}'\" value='{1}' /></form>".format(click, label)


def htmlDataTableMagic(tableId):
#----------------------------------------------------------------------------
# Html required to have a datatable table work, pass in the dom id
# See note below on trialData_wrapper
#
    r = '<link rel="stylesheet" type="text/css" href="//cdn.datatables.net/1.10.0/css/jquery.dataTables.css">'
    r += '\n<script type="text/javascript" language="javascript" src="//cdn.datatables.net/1.10.0/js/jquery.dataTables.js"></script>'
    r += '\n<script src={0}></script>'.format(url_for('static', filename='jquery.jeditable.css'))

    # We need to initialize the jquery datatable, but also a bit of hacking
    # to set the width of the page. We use the datatables scrollX init param
    # to get a horizontal scroll on the table, but it seems very hard in css to
    # get the table to fill the available screen space and not have the right
    # hand edge invisible off to the right of the page. You can set the width
    # of the dataTables_wrapper to a fixed amount and that works, but doesn't
    # reflect the actual window size. If you set the width to 100%, it just doesn't
    # work - partly it seems because we are using css tables (i.e. if I try the
    # same code NOT in these tables 100% does work. So we are doing here at the moment
    # is to (roughly) set the trialData_wrapper width to the appropriate size
    # after the datatable is initialized and hook up a handler to redo this whenever
    # the screen is resized. Not very nice or future proof, but it will have to do for
    # the moment..
    #
    # MFK 26/11/14: I've replaced the resize function, which was a call to setTrialDataWrapperWidth()
    # to be instead just a reload. This works better, setTrialDataWrapperWidth() was centering the table
    # rows without also centering the table headers. Hopefully the the reload is coming from the
    # cache rather than the network.
    #
    # NB trialData_wrapper is (I think!) the id of a div surrounding the table created
    # by the dataTable function.

    r += """
    <script>
    function setTrialDataWrapperWidth() {
        var w = window;
        var c = $(".dataContent").width();
        var leftBarWidth = $("#dataLeftBar").width();
        var setWidthTo = w.innerWidth - leftBarWidth - 60;
        //alert('w.width ' + w.innerWidth + ' ' + c + ' ' + setWidthTo);
        document.getElementById('trialData_wrapper').style.width = setWidthTo + 'px';
    }
    $(document).ready(
        function() {
            $("#%s").dataTable( {
                "scrollX": true,
                "fnPreDrawCallback":function(){
                    $("#%s").hide();
                    //$("#loading").show();
                },
                "fnDrawCallback":function(){
                    $("#%s").show();
                    //$("#loading").hide();
                },
                "fnInitComplete": function(oSettings, json) {$("#%s").show();}
            });
            setTrialDataWrapperWidth();
            //window.addEventListener('resize', setTrialDataWrapperWidth);
            window.addEventListener('resize', function () {
                "use strict";
                window.location.reload();
            });
        }
    );
    </script>
    """ % (tableId, tableId, tableId, tableId)
    return r

def htmlDatatable(headers, cols):
#
# Data table:
#
    numCols = len(headers)
    if numCols <= 0 or numCols != len(cols):
        return ''
    numRows = len(cols[0])
    r = htmlDataTableMagic('trialData')
    r += '<p><table id="trialData" class="display"  cellspacing="0" width="100%"  >'
    hdrs = ''
    for h in headers:
        hdrs += '<th>{0}</th>'.format(h)
    r += '<thead><tr>{0}</tr></thead>'.format(hdrs)
    r += '<tfoot><tr>{0}</tr></tfoot>'.format(hdrs)
    r += '<tbody>'
    for rowIndex in range(numRows):
        r += '<tr>'
        for col in cols:
            r += '<td>{0}</td>'.format(col[rowIndex])
        r += '</tr>'
    r += '</tbody>'
    r += '</table>'
    return r

def htmlDatatableByRow(headers, rows):
#
# Data table:
#
    out = htmlDataTableMagic('trialData')
    out += '<p><table id="trialData" class="display"  cellspacing="0" width="100%"  >'
    hdrs = ''
    for h in headers:
        hdrs += '<th>{0}</th>'.format(h)
    out += '<thead><tr>{0}</tr></thead>'.format(hdrs)
    out += '<tfoot><tr>{0}</tr></tfoot>'.format(hdrs)
    out += '<tbody>'
    for row in rows:
        out += '<tr>'
        for i in row:
            out += '<td>{0}</td>'.format(i)
        out += '</tr>'
    out += '</tbody>'
    out += '</table>'
    return out

