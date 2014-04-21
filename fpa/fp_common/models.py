#
# models.py
# Michael Kirk 2013
#
# Sqlalchemy models for the database.
#
# The models were originally autogenerated by sqlautocode
#

__all__ = ['Trial', 'TrialUnit', 'TrialUnitAttribute', 'AttributeValue', 'Datum', 'Trait']


#import sqlalchemy
from sqlalchemy import *
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, Session
from const import *
import util

### sqlalchemy CONSTANTS: ######################################################################

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata

attributeValue = Table(unicode(TABLE_ATTRIBUTE_VALUES), metadata,
    Column(u'trialUnitAttribute_id', INTEGER(), ForeignKey('trialUnitAttribute.id'), primary_key=True, nullable=False),
    Column(u'trialUnit_id', INTEGER(), ForeignKey('trialUnit.id'), primary_key=True, nullable=False),
    Column(unicode(AV_VALUE), TEXT(), nullable=False),
)

datum = Table(u'datum', metadata,
    Column(u'trialUnit_id', INTEGER(), ForeignKey('trialUnit.id'), primary_key=True, nullable=False),
    Column(u'traitInstance_id', INTEGER(), ForeignKey('traitInstance.id'), nullable=False),
    Column(u'timestamp', BigInteger(), primary_key=True, nullable=False),
    Column(u'gps_long', Float(asdecimal=True)),
    Column(u'gps_lat', Float(asdecimal=True)),
    Column(u'userid', TEXT()),
    Column(u'notes', TEXT()),
    Column(u'numValue', DECIMAL(precision=11, scale=3)),
    Column(u'txtValue', TEXT()),
)

traitInstance = Table(u'traitInstance', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False),
    Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), nullable=False),
    Column(u'dayCreated', INTEGER(), nullable=False),
    Column(u'seqNum', INTEGER(), nullable=False),
    Column(u'sampleNum', INTEGER(), nullable=False),
    Column(u'token', VARCHAR(length=31), nullable=False),
)

trialTrait = Table(u'trialTrait', metadata,
    Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False),
    Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False),
)


### sqlalchemy CLASSES: ######################################################################

class AttributeValue(DeclarativeBase):
    __table__ = attributeValue

    #relation definitions
    trialUnitAttribute = relation('TrialUnitAttribute', primaryjoin='AttributeValue.trialUnitAttribute_id==TrialUnitAttribute.id')
    trialUnit = relation('TrialUnit', primaryjoin='AttributeValue.trialUnit_id==TrialUnit.id')

    def setValueWithTypeUpdate(self, newVal):
    # Set the value, and if the val is not an integer, set the type to text.
        self.value = newVal
        if not util.isInt(newVal):
            self.trialUnitAttribute.datatype = T_STRING


class Datum(DeclarativeBase):
    __table__ = datum

    #relation definitions
    trialUnit = relation('TrialUnit', primaryjoin='Datum.trialUnit_id==TrialUnit.id')
    traitInstance = relation('TraitInstance', primaryjoin='Datum.traitInstance_id==TraitInstance.id')

    def getValue(self):
    #------------------------------------------------------------------
    # Return a value, how the value is stored/represented is type specific.
    # NB if the database value is null, then "NA" is returned.
        type = self.traitInstance.trait.type
        value = '?'
        if type == T_INTEGER: value = self.numValue
        if type == T_DECIMAL: value = self.numValue
        if type == T_STRING: value = self.txtValue
        if type == T_CATEGORICAL:
            value = self.numValue
            # Need to look up the text for the value:
            if value is not None:
                session = Session.object_session(self)
                traitId = self.traitInstance.trait.id
                trtCat = session.query(TraitCategory).filter(
                    and_(TraitCategory.trait_id == traitId, TraitCategory.value == value)).one()
                value = trtCat.caption
        if type == T_DATE: value = self.numValue
        if type == T_PHOTO: value = self.txtValue
        #if type == T_LOCATION: value = d.txtValue

        # Convert None to "NA"
        if value is None:
            value = "NA"
        return value

class Trait(DeclarativeBase):
    __tablename__ = 'trait'
    __table_args__ = {}

    #column definitions
    caption = Column(u'caption', VARCHAR(length=63), nullable=False)
    description = Column(u'description', TEXT(), nullable=False)
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    max = Column(u'max', DECIMAL(precision=10, scale=0))
    min = Column(u'min', DECIMAL(precision=10, scale=0))
    sysType = Column(u'sysType', INTEGER(), nullable=False)
    tid = Column(u'tid', TEXT())
    type = Column(u'type', INTEGER(), nullable=False)
    unit = Column(u'unit', TEXT())

    #relation definitions
    trials = relation('Trial', primaryjoin='Trait.id==trialTrait.c.trait_id', secondary=trialTrait, secondaryjoin='trialTrait.c.trial_id==Trial.id')
    categories = relation('TraitCategory')    # NB, only relevant for Categorical type

class TraitCategory(DeclarativeBase):
    __tablename__ = 'traitCategory'
    __table_args__ = {}

    #column definitions
    caption = Column(u'caption', TEXT(), nullable=False)
    imageURL = Column(u'imageURL', TEXT())
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    value = Column(u'value', INTEGER(), primary_key=True, nullable=False)

    #relation definitions
    trait = relation('Trait', primaryjoin='TraitCategory.trait_id==Trait.id')


class TraitInstance(DeclarativeBase):
    __table__ = traitInstance

    #relation definitions
    trait = relation('Trait', primaryjoin='TraitInstance.trait_id==Trait.id')
    trial = relation('Trial', primaryjoin='TraitInstance.trial_id==Trial.id')
    trialUnits = relation('TrialUnit', primaryjoin='TraitInstance.id==Datum.traitInstance_id', secondary=datum, secondaryjoin='Datum.trialUnit_id==TrialUnit.id')

class TrialTraitInteger(DeclarativeBase):
    __tablename__ = 'trialTraitInteger'
    max = Column(u'max', INTEGER())
    min = Column(u'min', INTEGER())
    cond = Column(u'validation', TEXT())
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False)

class TrialTraitNumeric(DeclarativeBase):
    __tablename__ = 'trialTraitInteger'
    max = Column(u'max', DECIMAL(precision=18, scale=9))
    min = Column(u'min', DECIMAL(precision=18, scale=9))
    cond = Column(u'validation', TEXT())
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False)

class Trial(DeclarativeBase):
    __tablename__ = 'trial'
    __table_args__ = {}

    #column definitions:
    acronym = Column(u'acronym', TEXT())
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=63), nullable=False)
    site = Column(u'site', TEXT())
    year = Column(u'year', TEXT())

    #relation definitions:
    traits = relation('Trait', primaryjoin='Trial.id==trialTrait.c.trial_id', secondary=trialTrait, secondaryjoin='trialTrait.c.trait_id==Trait.id')
    tuAttributes = relation('TrialUnitAttribute')
    trialUnits = relation('TrialUnit')

    def addOrGetNode(self, row, col):
        try:
            session = Session.object_session(self)
            tu = session.query(TrialUnit).filter(and_(TrialUnit.trial_id == self.id, TrialUnit.row == row,
                                                      TrialUnit.col == col)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            tu = TrialUnit()
            tu.row = row
            tu.col = col
            tu.trial_id = self.id
            session.add(tu)
            session.commit()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            return None

        return tu


class TrialUnit(DeclarativeBase):
    __tablename__ = 'trialUnit'
    __table_args__ = {}

    #column definitions
    barcode = Column(u'barcode', TEXT())
    col = Column(u'col', INTEGER(), nullable=False)
    description = Column(u'description', TEXT())
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    row = Column(u'row', INTEGER(), nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False)
    longitude = Column(u'longitude', Float(asdecimal=False))
    latitude = Column(u'latitude', Float(asdecimal=False))

    #relation definitions
    trial = relation('Trial', primaryjoin='TrialUnit.trial_id==Trial.id')
    trialUnitAttributes = relation('TrialUnitAttribute', primaryjoin='TrialUnit.id==AttributeValue.trialUnit_id',
                                   secondary=attributeValue, secondaryjoin='AttributeValue.trialUnitAttribute_id==TrialUnitAttribute.id')
    traitInstances = relation('TraitInstance', primaryjoin='TrialUnit.id==Datum.trialUnit_id', secondary=datum, secondaryjoin='Datum.traitInstance_id==TraitInstance.id')
    attVals = relation('AttributeValue')

class TrialUnitAttribute(DeclarativeBase):
    __tablename__ = 'trialUnitAttribute'
    __table_args__ = {}

    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=31), nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False)
    datatype = Column(unicode(TUA_DATATYPE), INTEGER(), default=T_INTEGER, nullable=False)
    func = Column(unicode(TUA_FUNC), INTEGER(), default=0, nullable=False)

    #relation definitions
    trial = relation('Trial', primaryjoin='TrialUnitAttribute.trial_id==Trial.id')
    trialUnits = relation('TrialUnit', primaryjoin='TrialUnitAttribute.id==AttributeValue.trialUnitAttribute_id', secondary=attributeValue, secondaryjoin='AttributeValue.trialUnit_id==TrialUnit.id')

class System(DeclarativeBase):
    __tablename__ = 'system'
    __table_args__ = {}
    name = Column(u'name', VARCHAR(length=63), primary_key=True, nullable=False)
    value = Column(u'value', VARCHAR(length=255), nullable=True)
    def __init__(self, name, value):
        self.name = name
        self.value = value

class TrialUnitNote(DeclarativeBase):
    __tablename__ = 'trialUnitNote'
    __table_args__ = {}

    #column definitions:
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    trialUnit_id = Column(u'trialUnit_id', INTEGER(), ForeignKey('trialUnit.id'), nullable=False)
    timestamp = Column(u'timestamp', BigInteger(), primary_key=True, nullable=False)
    userid = Column(u'userid', TEXT())
    note = Column(u'note', TEXT())
    token = Column(u'token', VARCHAR(length=31), nullable=False)

    #relation definitions:
    trialUnit = relation('TrialUnit', primaryjoin='TrialUnitNote.trialUnit_id==TrialUnit.id')


###  Functions:  ##################################################################################################

gdbg = True

def GetEngineForApp(targetUser):
#-----------------------------------------------------------------------
# This should be called once only and the result stored,
# currently done in session module.
#
    APPUSR = 'fpwserver'
    APPPWD = 'fpws_g00d10ch'
    dbname = 'fp_' + targetUser
    engine = create_engine('mysql://{0}:{1}@localhost/{2}'.format(APPUSR, APPPWD, dbname))
    Session = sessionmaker(bind=engine)
    dbsess = Session()
    return dbsess



# This should use alchemy and return connection
def DbConnectAndAuthenticate(username, password):
#-------------------------------------------------------------------------------------------------
    dbc = GetEngineForApp(username)    # not sure how this returns error, test..
    if dbc is None:
        return (None, 'Unknown user/database')

    # Check login:
    try:
        sysPwRec = dbc.query(System).filter(System.name == 'appPassword').one()
    except sqlalchemy.orm.exc.NoResultFound:
        # No password means OK to use:
        return dbc, None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        # Shouldn't happen:
        return None, 'DB error, multiple passwords'

    if sysPwRec.value == password:
        return dbc, None
    return None, 'Invalid password'


def GetTrial(dbc, trialid):
#-------------------------------------------------------------------------------------------------
    try:
        trl = dbc.query(Trial).filter(Trial.id == trialid).one()
    except sqlalchemy.exc.SQLAlchemyError, e:
        return None
    return trl


def GetTrialList(dbc):
#-------------------------------------------------------------------------------------------------
    try:
        trlList = dbc.query(Trial).all()
    except sqlalchemy.exc.SQLAlchemyError, e:
        return None
    return trlList


def GetOrCreateTraitInstance(dbc, traitID, trialID, seqNum, sampleNum, dayCreated, token):
#-------------------------------------------------------------------------------------------------
    # Get the trait instance, if it exists, else make a new one,
    # In either case, we need the id.
    # Note how trait instances from different devices are handled
    # Trait instances are uniquely identified by trial/trait/seqNum/sampleNum and token.
    tiSet = dbc.query(TraitInstance).filter(and_(
            TraitInstance.trait_id == traitID,
            TraitInstance.trial_id == trialID,
            TraitInstance.seqNum == seqNum,
            TraitInstance.sampleNum == sampleNum,
            TraitInstance.token == token
            )).all()
    if len(tiSet) == 1:
        dbTi = tiSet[0]
    elif len(tiSet) == 0:
        dbTi = TraitInstance()
        dbTi.trial_id = trialID
        dbTi.trait_id = traitID
        dbTi.dayCreated = dayCreated
        dbTi.seqNum = seqNum
        dbTi.sampleNum = sampleNum
        dbTi.token = token
        dbc.add(dbTi)
        dbc.commit()
    else:
        return None
    return dbTi


def AddTraitInstanceData(dbc, tiID, trtType, aData):
#-------------------------------------------------------------------------------------------------
# Return None for success, else an error message.
#
    valueFieldName = 'txtValue' if  trtType == 2 or trtType == 5 else 'numValue'
    qry = 'insert ignore into {0} ({1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}) values '.format(
        'datum', 'trialUnit_id', 'traitInstance_id',
        'timestamp', 'gps_long', 'gps_lat', 'userid',
        'notes', valueFieldName)
    for dat in aData:
        # have to see what format value is in in json, ideally string would be quoted,
        # and number not. note mysql should cope with quotes around numbers.
        valueField = ('"' + str(dat['value']) + '"') if 'value' in dat else 'null'
        notesField = ('"' + dat['notes'] + '"') if 'notes' in dat else 'null'
        try:
            qry += '({0}, {1}, {2}, {3}, {4}, "{5}", {6}, {7}),'.format(
                dat['trialUnit_id'], tiID, dat['timestamp'],
                dat['gps_long'], dat['gps_lat'], dat['userid'], notesField, valueField)
        except Exception, e:
            return 'Error parsing traitInstance:data ' + e.args[0]

    # NB we are assuming there is at least one datum (we checked for this above):
    qry = qry[:-1] # Fix up last char:

    # call sql to do multi insert:  Need to import LogDebug func for this
    # if gdbg:
    #     LogDebug("sql qry", qry)
    dbc.bind.execute(qry)

    return None;


def AddTrialUnitNotes(dbc, token, notes):
#-------------------------------------------------------------------------------------------------
# Return None for success, else an error message.
#
    qry = 'insert ignore into {0} ({1}, {2}, {3}, {4}, {5}) values '.format(
        'trialUnitNote', 'trialUnit_id', 'timestamp', 'userid', 'token', 'note')
    if len(notes) <= 0:
        return None
    for n in notes:
        try:
            qry += '({0}, {1}, "{2}", "{3}", "{4}"),'.format(
                n['trialUnit_id'], n['timestamp'], n['userid'], token, n['note'])
        except Exception, e:
            return 'Error parsing note ' + e.args[0]

    qry = qry[:-1] # Remove last comma
    # call sql to do multi insert:
    # if gdbg: LogDebug("sql qry", qry)
    dbc.bind.execute(qry)
    return None;


def CreateTrait2(dbc, caption, description, vtype, sysType, vmin, vmax):
#--------------------------------------------------------------------------
# Creates a trait with the passed values and writes it to the db.
# Returns a list [ <new trait> | None, ErrorMessage | None ]
# NB doesn't add to trialTrait table
# Currently only written with adhoc traits in mind..
#
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.
    ntrt = Trait()
    ntrt.caption = caption
    ntrt.description = description
    ntrt.sysType = sysType

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    # and add to trialTrait?
    if sysType == SYSTYPE_TRIAL: # If local, check there's no other trait local to the trial with the same caption:
        # trial = GetTrialFromDBsess(sess, tid)
        # for x in trial.traits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        # ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        pass
    elif sysType == SYSTYPE_SYSTEM:  # If system trait, check there's no other system trait with same caption:
        # sysTraits = dbUtil.GetSysTraits(sess)
        # for x in sysTraits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        pass
    elif sysType == SYSTYPE_ADHOC:
        # Check no trait with same caption that's not an adhoc trait for another device
        # Do adhoc traits go into trialTrait?
        # Perhaps not at the moment, but perhaps they should be..
        pass
    else:
        return (None, "Invalid sysType")

    ntrt.type = vtype
    if vmin:
        ntrt.min = vmin
    if vmax:
        ntrt.max = vmax
    dbc.add(ntrt)
    dbc.commit()
    return ntrt, None


def GetTrialTraitIntegerDetails(dbc, trait_id, trial_id):
    tti = dbc.query(TrialTraitInteger).filter(and_(
            TrialTraitInteger.trait_id == trait_id,
            TrialTraitInteger.trial_id == trial_id
            )).all()
    if len(tti) == 1:
        ttid = tti[0]
        return ttid
    return None
def GetTrialTraitNumericDetails(dbc, trait_id, trial_id): #replace above with this if poss
# Return TrialTraitNumeric for specified trait/trial, or None if none exists.
    tti = dbc.query(TrialTraitNumeric).filter(and_(
            TrialTraitNumeric.trait_id == trait_id,
            TrialTraitNumeric.trial_id == trial_id
            )).all()
    if len(tti) == 1:
        ttid = tti[0]
        return ttid
    return None

# def LogDebug(hdr, text):
# #-------------------------------------------------------------------------------------------------
# # Writes stuff to file system (for debug)
#     from datetime import datetime
#     f = open('/tmp/fieldPrimeDebug','a')
#     print >>f, "--- " + str(datetime.now()) + " " + hdr + ": -------------------"
#     print >>f, text
#     f.close
