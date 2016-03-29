#
# forms.py
# Michael Kirk 2016
# Form support.
#
#


#
# class formElement
# Class for element to go on html form. Element defined by
# a few parameters, html can then be produced.
# MFK this should probably be in on file, rather than just used
# for the single trialProperties form.
#
class formElement:
    # Supported element types:
    TEXT = 1
    RADIO = 2

    def __init__(self, prompt, subPrompt, ename, eid, dbName=None, etype=TEXT, typeSpecificData=None, default=None):
        self.prompt = prompt
        self.subPrompt = subPrompt
        self.ename = ename
        self.eid = eid
        self.dbName = dbName if dbName is not None else ename
        self.etype = etype
        self.typeSpecificData = typeSpecificData
        self.default=default

    def __wrapElement(self, element):
        return '''
            <tr>
              <td>
                <label>{0}<span class="small">{1}</span></label>
              </td>
              <td>
                {2}
              </td>
            </tr>
            '''.format(self.prompt, self.subPrompt, element)

    def htmlElement(self, value=None):
        #------------------------------------------------------------------
        # Html string giving table record for display by newTrial.html. Note
        # this is not ideal, as we have the preferred display details both here
        # and in newTrial.html. Ideally this would be all here or all there.
        # Here is currently used for dynamically determined elements while
        # newTrial.html has the trial attributes that are in all trials.
        # NB Javascript validation function is also in newTrial.html
        #
        element = ''
        if self.etype == self.TEXT:
            if value is None and self.typeSpecificData is not None:
                value = self.typeSpecificData
            element = '''
                   <input type="text" id='{0}' name="{1}" {2}>
                '''.format(self.eid, self.ename,
                           ' value="{0}"'.format(value) if value is not None else '')
        elif self.etype == self.RADIO:
            if value is None and self.default is not None:
                value = self.default
            element += '<div class="uifDiv">'
            for key in self.typeSpecificData:
                val = self.typeSpecificData[key]
                #print 'val {0} value {1} equal {2} {3} {4}'.format(val, value, 'yes' if val==value else 'no', type(val), type(value))
                element += '<input class="nostyle" type="radio" name="{0}" value="{1}" {2}>{3}'.format(
                    self.ename, val, 'checked' if val == value else '', key)
            element += '</div>'
        return self.__wrapElement(element)


def makeForm(formElements):
    out = '<form><table class="userInputForm">'
    for el in formElements:
        out += el.htmlElement()
    out += '</table></form>'
    return out

def makeModalForm(buttonLabel, formElements, divId="myModal", action=None):
# Returns html for modal form. Initially only a button (with given label) is
# visible. Pressing the button presents a modal form with the given elements.
# If more than one form is to be used on a single page, they must each have unique divId.
#    
    out = '<button type="button" class="btn btn-primary" data-toggle="modal" data-target="#{}">'.format(divId)
    out += '{}</button>'.format(buttonLabel)
    out += '<div id="{}" class="modal fade" role="dialog"><div class="modal-dialog"><div class="modal-content">'.format(divId)

    # modal header:
    out += '''<div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h4 class="modal-title">{}</h4>
      </div>'''.format(buttonLabel)

    # modal content:
    out += '<div class="modal-body">'
    out += '<form method="post" {}><table class="userInputForm">'.format("" if action is None else action)
    for el in formElements:
        out += el.htmlElement()
    out += '</table><input type="submit" value="Submit"></form>'
    out += '</div>'

    # modal footer:
    out += '''<div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>'''

    out += '</div></div></div>'
    return out
