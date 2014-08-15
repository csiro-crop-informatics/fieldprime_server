# dbUtil.py
# Michael Kirk 2013
#
#
#

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation

from functools import wraps

from fp_common.models import Trial, Trait, TrialTrait, TrialUnit, TrialUnitAttribute, \
    AttributeValue, TraitInstance, Datum, TrialUnitNote, TraitCategory, \
    SYSTYPE_SYSTEM, System


#############################################################################################
###  FUNCTIONS: #############################################################################

def GetEngine(sess):
#-----------------------------------------------------------------------
# This should be called once only and the result stored,
# currently done in session module.
#
    fpUser = 'fp_' + sess.GetUser()
    engine = create_engine('mysql://{0}:{1}@localhost/{2}'.format(fpUser, sess.GetPassword(), fpUser))
    Session = sessionmaker(bind=engine)   # Create sessionmaker instance
    dbsess = Session()                    # Create a session
    return dbsess

def oneException2None(func):
#--------------------------------------------------------------------
# Decorator used for sqlalchemy one() queries, which throw exceptions if
# there isn't exactly one result. This function traps the exceptions, it
# returns the result if exactly one is found, else None.
#
    @wraps(func)
    def with_traps(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        except sqlalchemy.orm.exc.MultipleResultsFound:
            return None
        return ret
    return with_traps

def GetTrials(sess):
    return sess.DB().query(Trial).all()

@oneException2None
def GetTrial(sess, trialID):
#-----------------------------------------------------------------------
# Returns trial object for given id if found, else None.
    return sess.DB().query(Trial).filter(Trial.id == trialID).one()

@oneException2None
def getSystemValue(sess, name):
    return sess.DB().query(System).filter(System.name == name).one().value

def setSystemValue(sess, name, value):
#-----------------------------------------------------------------------
# Insert or update new system value.
    sysItem = System(name, value)
    sysItem = sess.DB().merge(sysItem)
    sess.DB().commit()

def GetTrait(sess, traitId):
    return sess.DB().query(Trait).filter(Trait.id == traitId).one()

def getTrialTrait(sess, trialId, traitId):
    return sess.DB().query(TrialTrait).filter(
        and_(TrialTrait.trait_id == traitId, TrialTrait.trial_id == trialId)).one()

@oneException2None
def getTraitCategory(sess, traitId, value):
    return sess.DB().query(TraitCategory).filter(
        and_(TraitCategory.trait_id == traitId, TraitCategory.value == value)).one()

def GetTrialFromDBsess(sess, trialID):
    return sess.DB().query(Trial).filter(Trial.id == trialID).one()

def GetTraitInstancesForTrial(sess, trialID):
#-----------------------------------------------------------------------
# Return all the traitInstances for the specified trial,
# ordered by trait, token, seqnum, samplenum.
    return sess.DB().query(TraitInstance).filter(
        TraitInstance.trial_id == trialID).order_by(
        TraitInstance.trait_id, TraitInstance.token, TraitInstance.seqNum, TraitInstance.sampleNum).all()

def GetTrialAttributes(sess, trialID):
    return sess.DB().query(TrialUnitAttribute).filter(
        TrialUnitAttribute.trial_id == trialID).order_by(TrialUnitAttribute.name).all()

def GetAttribute(sess, attId):
    return sess.DB().query(TrialUnitAttribute).filter(TrialUnitAttribute.id == attId).one()

def getNodes(sess, trialId):
#-----------------------------------------------------------------------
# Return nodes for the specified trial, sorted by row/col
    return sess.DB().query(TrialUnit).filter(TrialUnit.trial_id==trialId).order_by(TrialUnit.row, TrialUnit.col).all()

@oneException2None
def getNode(sess, nodeId):
#-----------------------------------------------------------------------
# Return node with the given id. MFK Dupe with models.getNode, as is other stuff in here..
    return sess.DB().query(TrialUnit).filter(TrialUnit.id==nodeId).one()

@oneException2None
def getAttributeValue(sess, trialUnitId, trialUnitAttributeId):
    return sess.DB().query(AttributeValue).filter(
        and_(
            AttributeValue.trialUnit_id == trialUnitId,
            AttributeValue.trialUnitAttribute_id == trialUnitAttributeId)
        ).one()

def GetAttributeValues(sess, trialUnitAttributeId):
    return sess.DB().query(AttributeValue).filter(AttributeValue.trialUnitAttribute_id == trialUnitAttributeId).all()

def GetTrialUnit(sess, trialId, row, col):
    return sess.DB().query(TrialUnit).filter(and_(TrialUnit.trial_id == trialId, TrialUnit.row == row, TrialUnit.col == col)).one()

def addOrGetNode(sess, trialId, row, col):
# Retrieve node for specified trial/row/col, creating a new one
# if not already present.
    try:
        tu = sess.DB().query(TrialUnit).filter(and_(TrialUnit.trial_id == trialId, TrialUnit.row == row,
                                                  TrialUnit.col == col)).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        return None

def GetDatum(sess, trialUnit_id, traitInstance_id):
    return sess.DB().query(Datum).filter(and_(Datum.trialUnit_id == trialUnit_id, Datum.traitInstance_id == traitInstance_id)).all()

def GetSysTraits(sess):
    return sess.DB().query(Trait).filter(Trait.sysType == SYSTYPE_SYSTEM).all()

def GetTrialUnitNotes(sess, trialUnit_id):
    return sess.DB().query(TrialUnitNote).filter(TrialUnitNote.trialUnit_id == trialUnit_id).all()

def getTraitInstance(sess, traitInstance_id):
    return sess.DB().query(TraitInstance).filter(TraitInstance.id == traitInstance_id).one()

def getTraitInstanceData(sess, traitInstance_id):
    return sess.DB().query(Datum).filter(Datum.traitInstance_id == traitInstance_id).all()

