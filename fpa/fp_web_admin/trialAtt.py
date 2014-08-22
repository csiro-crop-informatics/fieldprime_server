#
# trialAtt.py
# Michael Kirk 2014
# Provides a trial attribute class and a list of them.
# Allowed trial attributes are statically determined (by this file).
#


#
# class trialAttHtmlElement
# NOT a database class, but a container for a set of traitInstances that
# make up a scoreSet
#
class trialAttHtmlElement:
    def __init__(self, prompt, subPrompt, ename, eid, dbName=None):
        self.prompt = prompt
        self.subPrompt = subPrompt
        self.ename = ename
        self.eid = eid
        self.dbName = dbName if dbName is not None else ename

    def htmlElement(self):
        #------------------------------------------------------------------
        # Html string giving table record for display by newTrial.html. Note
        # this is not ideal, as we have the preferred display details both here
        # and in newTrial.html. Ideally this would be all here or all there.
        # Here is currently used for dynamically determined elements while
        # newTrial.html has the trial attributes that are in all trials.
        #
        out = '''
            <tr>
              <td >
                <label>{0}<span class="small">{1}</span></label>
              </td>
              <td >
                <input type="text" id='{2}' name="{3}">
              </td>
            </tr>
            '''.format(self.prompt, self.subPrompt, self.eid, self.ename)
        return out

# Trial attribute list:
gTrialAttributes = [trialAttHtmlElement('NodeCreation', 'Allow node creation from app', 'ncid', 'ncname')]
#gTrialAttributes = [trialAttHtmlElement('hey', 'give us a hey', 'heyid', 'heyname'),
#          trialAttHtmlElement('ho', 'give us a ho!', 'hoid', 'honame')]

