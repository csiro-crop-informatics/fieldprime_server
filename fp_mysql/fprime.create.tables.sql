-- 
-- SQL statements to create tables for an fprime instance.
-- NB, assumes database is created and used.
-- 
-- -----------------------------------------------------------------------------------------------------


--
-- system
-- Only relevant to the android app at the moment
-- in particular used to store a password that the device must
-- use to access the database.
--
create table system(
  name	VARCHAR(63) PRIMARY KEY,
  value VARCHAR(255)
);

--
-- trial
--
create table trial(
  id       INT PRIMARY KEY AUTO_INCREMENT,
  name     VARCHAR(63) UNIQUE NOT NULL,
  site     text,
  year     text,
  acronym  text
);


--
-- trialUnit
-- Each trial has a set of trialUnits (eg plots)
-- NB, the text attributes will be moved to another table,so as to allow
-- an arbritrary (user specified) set of attributes.
-- So genotype, pedigree, and barcode will be removed (and possibly description).
-- All trial unit attributes other than the mandatory first four will be stored
-- via the trialUnitAttribute and attributeValue tables.
-- 
create table trialUnit(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  trial_id    INT NOT NULL,
  row         INT NOT NULL,
  col         INT NOT NULL,
  description text,
  barcode     text,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);

-- 
-- trialUnitAttribute
--
-- To allow for arbitrary extra trial unit attributes, not anticipated at design time.
-- 
create table trialUnitAttribute(
  id         INT PRIMARY KEY AUTO_INCREMENT,
  trial_id   INT NOT NULL,
  name       VARCHAR(31) NOT NULL,
  UNIQUE (trial_id, name),
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);


--
-- trialUnitNote
-- The uniqueness constraint (may be) required to prevent storing multiple uploads
-- of the same note from a device (data upload should be idempotent if the data hasn't
-- changed).
--
create table trialUnitNote(
  id            INTEGER PRIMARY KEY AUTO_INCREMENT,
  trialUnit_id  INTEGER,
  timestamp     BIGINT NOT NULL,
  userid        text,
  note          text,
  UNIQUE (trialUnit_id, timestamp, note(100)),
  FOREIGN KEY(trialUnit_id) REFERENCES trialUnit(id) ON DELETE CASCADE
);


-- 
-- attributeValues
--
create table attributeValues(
  trialUnitAttribute_id   integer NOT NULL,
  trialUnit_id            integer NOT NULL,
  value                   text NOT NULL,
  PRIMARY KEY(trialUnitAttribute_id, trialUnit_id),
  FOREIGN KEY(trialUnitAttribute_id) REFERENCES trialUnitAttribute(id) ON DELETE CASCADE,
  FOREIGN KEY(trialUnit_id) REFERENCES trialUnit(id) ON DELETE CASCADE
);

--
-- trait
--
create table trait(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  caption     VARCHAR(63) NOT NULL,
  description text NOT NULL,
  type        INT NOT NULL,
  sysType     INT NOT NULL,
  tid         text,
  unit        text,
  min         decimal,
  max         decimal
);


--
-- traitCategory
--
-- Values for categorical trait
-- could have: image as blob, but currently just a file reference.
--
create table traitCategory(
  trait_id    INT NOT NULL,
  value       INT NOT NULL,
  caption     text NOT NULL,
  imageURL    text,
  PRIMARY KEY(trait_id, value),
  FOREIGN KEY(trait_id) REFERENCES trait(id)
);


--
-- trialTrait
-- Records the traits associated with each trial.
--
create table trialTrait(
  trial_id   INT NOT NULL,
  trait_id   INT NOT NULL,
  PRIMARY KEY(trial_id, trait_id),
  FOREIGN KEY(trait_id) REFERENCES trait(id),
  FOREIGN KEY(trial_id) REFERENCES trial(id)
);


--
-- traitInstance
-- MFK should add Android ID?
--
create table traitInstance(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  trial_id    INT NOT NULL,
  trait_id    INT NOT NULL,
  dayCreated  INT NOT NULL,
  seqNum      INT NOT NULL,
  sampleNum   INT NOT NULL,
  token       VARCHAR(31) NOT NULL,
  UNIQUE(trial_id, trait_id, seqNum, sampleNum, token),
  FOREIGN KEY(trait_id) REFERENCES trait(id),
  FOREIGN KEY(trial_id) REFERENCES trial(id)
);


--
-- datum
--
-- Data value for trialUnit/traitInstance:
-- Intended to support multiple kinds of data, hence muliple value
-- fields. Currently only text and numeric, but we may have to add a blog
-- type value to cover all possibilities.
-- NB numValue has to hold values like 20130101
--
create table datum(
  trialUnit_id     INT NOT NULL,
  traitInstance_id INT NOT NULL,
  timestamp        BIGINT NOT NULL,
  gps_long         DOUBLE,
  gps_lat          DOUBLE,
  userid           text,
  notes            text,
  numValue         DECIMAL(11,3),
  txtValue         text,
  PRIMARY KEY(trialUnit_id, traitInstance_id, timestamp),
  FOREIGN KEY(trialUnit_id) REFERENCES trialUnit(id),
  FOREIGN KEY(traitInstance_id) REFERENCES traitInstance(id)
);

