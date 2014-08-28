#
# trialAtt.py
# Michael Kirk 2014
# Provides a trial attribute class and a list of them.
# Allowed trial attributes are statically determined (by this file).
#

import fp_common.models as models


#
# class trialAttHtmlElement
# NOT a database class, but a container for a set of traitInstances that
# make up a scoreSet
#
class trialAttHtmlElement:
    def __init__(self, prompt, subPrompt, ename, eid, dbName=None, etype='text'):
        self.prompt = prompt
        self.subPrompt = subPrompt
        self.ename = ename
        self.eid = eid
        self.dbName = dbName if dbName is not None else ename
        self.etype = etype

    def htmlElement(self, value=None):
        #------------------------------------------------------------------
        # Html string giving table record for display by newTrial.html. Note
        # this is not ideal, as we have the preferred display details both here
        # and in newTrial.html. Ideally this would be all here or all there.
        # Here is currently used for dynamically determined elements while
        # newTrial.html has the trial attributes that are in all trials.
        # NB Javascript validation function is also in newTrial.html
        #

        out = '''
            <tr>
              <td>
                <label>{0}<span class="small">{1}</span></label>
              </td>
              <td>
                <input type="text" id='{2}' name="{3}" {4}>
              </td>
            </tr>
            '''.format(self.prompt, self.subPrompt, self.eid, self.ename,
                       ' value="{0}"'.format(value) if value is not None else '')
        return out


# Trial attribute list:
gTrialAttributes = [trialAttHtmlElement('NodeCreation', 'Allow node creation from app', 'nodeCreation', 'ncid')]
#gTrialAttributes = [trialAttHtmlElement('hey', 'give us a hey', 'heyid', 'heyname'),
#          trialAttHtmlElement('ho', 'give us a ho!', 'hoid', 'honame')]

def trialPropertyTable(sess, trial, create=True):
# Returns html form elements for the current allowed set of trial properties.
# If create is true then also the hard-wired trial properties (i.e. those in the
# trial table, not the trialAtt table) are also included.
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
            value = models.TrialAtt.getPropertyValue(sess.DB(), trial.id, tae.dbName)
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


