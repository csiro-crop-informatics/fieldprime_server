#
# trialProperties.py
# Michael Kirk 2014
# Provides a trial attribute class and a list of them.
# Allowed trial attributes are statically determined (by this file).
#

import fp_common.models as models
import fp_common.const as fpconst
from forms import formElement


# Trial attribute list:
# MFK this needs to be an instance of a class, not a global, and passed into trialPropertyTable
gTrialAttributes = [
    formElement('NodeCreation', 'Allow node creation from app',
                'nodeCreation', 'ncid',
                etype=formElement.RADIO,
                typeSpecificData={'yes':'true', 'no':'false'}),
    formElement('Row alias', 'Word to use for rows',
               fpconst.INDEX_NAME_1, 'rowNameId',
               etype=formElement.TEXT, typeSpecificData='Row'),  #MFK constants for "row" "column"?
    formElement('Column alias', 'Word to use for columns',
                fpconst.INDEX_NAME_2, 'rowNameId',
                etype=formElement.TEXT, typeSpecificData='Column')
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



