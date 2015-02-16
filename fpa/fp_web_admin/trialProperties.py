#
# trialProperties.py
# Michael Kirk 2014
# Provides a trial attribute class and a list of them.
# Allowed trial attributes are statically determined (by this file).
#

import fp_common.models as models


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

    def __init__(self, prompt, subPrompt, ename, eid, dbName=None, etype=TEXT, typeSpecificData=None):
        self.prompt = prompt
        self.subPrompt = subPrompt
        self.ename = ename
        self.eid = eid
        self.dbName = dbName if dbName is not None else ename
        self.etype = etype
        self.typeSpecificData = typeSpecificData

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
            element = '''
                   <input type="text" id='{0}' name="{1}" {2}>
                '''.format(self.eid, self.ename,
                           ' value="{0}"'.format(value) if value is not None else '')
        elif self.etype == self.RADIO:
            element += '<div class="uifDiv">'
            for key in self.typeSpecificData:
                val = self.typeSpecificData[key]
                #print 'val {0} value {1} equal {2} {3} {4}'.format(val, value, 'yes' if val==value else 'no', type(val), type(value))
                element += '<input class="nostyle" type="radio" name="{0}" value="{1}" {2}>{3}'.format(
                    self.ename, val, 'checked' if val == value else '', key)
            element += '</div>'
        return self.__wrapElement(element)


# Trial attribute list:
# MFK this needs to be an instance of a class, not a global, and passed into trialPropertyTable
gTrialAttributes = [
    formElement('NodeCreation', 'Allow node creation from app',
                'nodeCreation', 'ncid',
                etype=formElement.RADIO,
                typeSpecificData={'yes':'true', 'no':'false'})
]


def trialPropertyTable(sess, trial, create=True):
# Returns html form elements for the current allowed set of trial properties.
# If create is true then also the hard-wired trial properties (i.e. those in the
# trial table, not the trialProperty table) are also included.
#
    out = '<table class="userInputForm">'
    if create:
        out += '''
      <table>
        <tr>
          <td >
            <label>Name<span class="small">Add a trial name (mandatory)</span></label>
          </td>
          <td >
            <input type="text" id='name_id' name="name">
          </td>
        </tr>
        <tr>
          <td >
            <label>Site<span class="small">(optional)</span></label>
          </td>
          <td >
            <input type="text" name="site"><br>
          </td>
        </tr>
        <tr>
          <td >
            <label>Year<span class="small">(optional)</span></label>
          </td>
          <td >
            <input type="text" name="year"><br>
          </td>
        </tr>
        <tr>
          <td >
            <label>Acronym<span class="small">(optional)</span></label>
          </td>
          <td >
            <input type="text" name="acronym"><br>
          </td>
        </tr>
        '''

    # Add the modifiable fields:
    for tae in gTrialAttributes:
        value = None
        if not create:
            # get value
            value = models.TrialProperty.getPropertyValue(sess.db(), trial.id, tae.dbName)
        out += tae.htmlElement(value)

    if create:
        out += '''
        <tr>
          <td>
            <label>Trial Plan CSV File<span class="small">List of trial nodes, and attributes (mandatory)</span></label>
          </td>
          <td>
            <input type="file" id='uploadFile_id' name="file">
          </td>
        </tr>
       '''

    out += '</table>\n'
    return out

def processPropertiesForm(sess, trialId, form):
    for tae in gTrialAttributes:
        # trying to insert or update
        newProp = models.TrialProperty(trialId, tae.dbName, form.get(tae.ename))
        newProp = sess.db().merge(newProp)
    sess.db().commit()



