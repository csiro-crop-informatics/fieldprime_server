# dbUtil.py
# Michael Kirk 2013
#
#
#


import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fp_common.models import Trial, Trait, TrialUnit, TrialUnitAttribute, \
    AttributeValue, TraitInstance, Datum, TrialUnitNote, TraitCategory, SYSTYPE_SYSTEM

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation


#-- CONSTANTS: ---------------------------------------------------------------------


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

def GetTrials(sess):
    return sess.DB().query(Trial).all()

def GetTrial(sess, trialID):
    return sess.DB().query(Trial).filter(Trial.id == trialID).one()

def GetTrait(sess, traitId):
    return sess.DB().query(Trait).filter(Trait.id == traitId).one()

def GetTraitCategory(sess, traitId, value):
    return sess.DB().query(TraitCategory).filter(
        and_(TraitCategory.trait_id == traitId, TraitCategory.value == value)).one()

def GetTrialFromDBsess(sess, trialID):
    return sess.DB().query(Trial).filter(Trial.id == trialID).one()

def GetTraitInstancesForTrial(sess, trialID):
    return sess.DB().query(TraitInstance).filter(
        TraitInstance.trial_id == trialID).order_by(
        TraitInstance.trait_id, TraitInstance.seqNum, TraitInstance.sampleNum).all()

def GetTrialAttributes(sess, trialID):
    return sess.DB().query(TrialUnitAttribute).filter(TrialUnitAttribute.trial_id == trialID).all()

def GetAttribute(sess, attId):
    return sess.DB().query(TrialUnitAttribute).filter(TrialUnitAttribute.id == attId).one()

def GetAttributeValue(sess, trialUnitId, trialUnitAttributeId):
    try:
        av = sess.DB().query(AttributeValue).filter(
            and_(
                AttributeValue.trialUnit_id == trialUnitId,
                AttributeValue.trialUnitAttribute_id == trialUnitAttributeId)
            ).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        return None
    return av

def GetAttributeValues(sess, trialUnitAttributeId):
    return sess.DB().query(AttributeValue).filter(AttributeValue.trialUnitAttribute_id == trialUnitAttributeId).all()

def GetTrialUnits(sess, trialID):
    return sess.DB().query(TrialUnit).filter(TrialUnit.trial_id == trialID).all()

def GetTrialUnit(sess, trialId, row, col):
    return sess.DB().query(TrialUnit).filter(and_(TrialUnit.trial_id == trialId, TrialUnit.row == row, TrialUnit.col == col)).one()

def GetDatum(sess, trialUnit_id, traitInstance_id):
    return sess.DB().query(Datum).filter(and_(Datum.trialUnit_id == trialUnit_id, Datum.traitInstance_id == traitInstance_id)).all()

def GetSysTraits(sess):
    return sess.DB().query(Trait).filter(Trait.sysType == SYSTYPE_SYSTEM).all()

def GetTrialUnitNotes(sess, trialUnit_id):
    return sess.DB().query(TrialUnitNote).filter(TrialUnitNote.trialUnit_id == trialUnit_id).all()
