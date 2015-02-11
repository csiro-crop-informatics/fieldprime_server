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
-- trialAtt
--
-- Place to store additional per trial info without needing to alter
-- table structures (att short for attribute).
-- Currently allow only one value for each trial/name. We could
-- change this if necessary, but note some code, attow, relies
-- on this property and would need changing if this changed.
--
create table trialProperty(
  trial_id    integer not null,
  name        varchar(63) not null,
  value       text,
  PRIMARY KEY (trial_id, name),
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);


--
-- node
-- Each trial has a set of nodes (eg plots)
-- NB, the text attributes will be moved to another table,so as to allow
-- an arbritrary (user specified) set of attributes.
-- So genotype, pedigree, and barcode will be removed (and possibly description).
-- All trial unit attributes other than the mandatory first four will be stored
-- via the nodeAttribute and attributeValue tables.
--
create table node(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  trial_id    INT NOT NULL,
  row         INT NOT NULL,
  col         INT NOT NULL,
  description text,
  barcode     text,
  latitude    DOUBLE,
  longitude   DOUBLE,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);


--
-- nodeAttribute
--
-- To allow for arbitrary extra trial unit attributes, not anticipated at design time.
--
create table nodeAttribute(
  id         INT PRIMARY KEY AUTO_INCREMENT,
  trial_id   INT NOT NULL,
  name       VARCHAR(127) NOT NULL,
  datatype   INT NOT NULL DEFAULT 2,
  func       INT NOT NULL DEFAULT 0,
  UNIQUE (trial_id, name),
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);

--
-- nodeNote
-- The uniqueness constraint (may be) required to prevent storing multiple uploads
-- of the same note from a device (data upload should be idempotent if the data hasn't
-- changed).
--
create table nodeNote(
  id            INTEGER PRIMARY KEY AUTO_INCREMENT,
  node_id  INTEGER,
  timestamp     BIGINT NOT NULL,
  userid        text,
  token         VARCHAR(31) NOT NULL,
  note          text,
  UNIQUE (node_id, timestamp, note(100)),
  FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
);

--
-- attributeValue
--
create table attributeValue(
  nodeAttribute_id   integer NOT NULL,
  node_id            integer NOT NULL,
  value                   text NOT NULL,
  PRIMARY KEY(nodeAttribute_id, node_id),
  FOREIGN KEY(nodeAttribute_id) REFERENCES nodeAttribute(id) ON DELETE CASCADE,
  FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
);

--
-- trait
--
-- future:
-- change "type" to "datatype"
-- download  boolean  (can go to devices)
-- readonly  boolean  (no modification/creation on the devices, only relevant if download)
-- single    boolean  (only allow single traitInstance)
--
create table trait(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  caption     VARCHAR(63) NOT NULL,
  description text NOT NULL,
  type        INT NOT NULL,
  sysType     INT NOT NULL
-- The following are no longer used, I think:
--  tid         text,
--  unit        text,
--  min         decimal,
--  max         decimal,
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
  FOREIGN KEY(trait_id) REFERENCES trait(id) ON DELETE CASCADE
);


--
-- trialTrait
-- Records the traits associated with each trial.
-- Also attributes specific to a trialTrait, but not the trait type.
--
create table trialTrait(
  trial_id   INT NOT NULL,
  trait_id   INT NOT NULL,
  barcodeAtt_id integer,
  PRIMARY KEY(trial_id, trait_id),
  FOREIGN KEY(trait_id) REFERENCES trait(id) ON DELETE CASCADE,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE,
  FOREIGN KEY(barcodeAtt_id) REFERENCES nodeAttribute(id)
);


--
-- trialTraitNumeric
-- Extension of trialTrait table intended for decimal and integer traits.
-- Should this instead refer to key of trialTrait?
-- See comment on traitString table.
--
create table trialTraitNumeric(
  trial_id   INT NOT NULL,
  trait_id   INT NOT NULL,
  min        DECIMAL(18,9),
  max        DECIMAL(18,9),
  validation TEXT,
  PRIMARY KEY(trial_id, trait_id),
  FOREIGN KEY(trait_id) REFERENCES trait(id) ON DELETE CASCADE,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);

--
-- traitString
-- Extension of trialTrait table for string traits,
-- NB this should perhaps be called trialTraitString, since the
-- key is the combination of trial and trait. However, I suspect
-- that eventually a trait may becomes specific to a trial (i.e.
-- if we want the same trait in a different trial that will be a
-- separate record, perhaps copied, in the trait table). And traitString
-- is shorter to type, and also matches the table name used in the
-- app, where traits already have a unique trial. Note the inconsistency
-- with trialTraitNumeric, and indeed the existence of table trialTrait.
-- These perhaps will have to be changed.
--
create table traitString(
  trial_id   INT NOT NULL,
  trait_id   INT NOT NULL,
  pattern    TEXT,
  PRIMARY KEY(trial_id, trait_id),
  FOREIGN KEY(trait_id) REFERENCES trait(id) ON DELETE CASCADE,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);

--
-- traitInstance
-- A traitInstance is uniquely identified by trial/trait/seqNum/sampleNum/token.
-- They are grouped into score set by trial/trait/seqNum/token.
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
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);


--
-- token
-- Represents server token used to identify client trial downloads.
-- The token is a composite of the android device id, and the time
-- the trial was downloaded to it. We may want in the future to have
-- a separate table for android id, and then this table would have
-- an id of a androidId table record, and the timestamp field.
--
create table token(
  id          INT PRIMARY KEY AUTO_INCREMENT,
  token       VARCHAR(31) NOT NULL UNIQUE,
  trial_id    INT,
  FOREIGN KEY(trial_id) REFERENCES trial(id) ON DELETE CASCADE
);

--
-- tokenNode
-- Used to record nodes created from devices, so as to avoid creating multiple copies.
-- Note localId is not called local_id because it is not a foreign key, it is from the client.
--
create table tokenNode(
  token_id   INT NOT NULL,
  localId    INT NOT NULL,
  node_id    INT NOT NULL,
  PRIMARY KEY(token_id, localId),
  FOREIGN KEY(token_id) REFERENCES token(id)
);

--
-- datum
--
-- Data value for node/traitInstance:
-- Intended to support multiple kinds of data, hence muliple value
-- fields. Currently only text and numeric, but we may have to add a blog
-- type value to cover all possibilities.
-- NB numValue has to hold values like 20130101
--
create table datum(
  node_id     INT NOT NULL,
  traitInstance_id INT NOT NULL,
  timestamp        BIGINT NOT NULL,
  gps_long         DOUBLE,
  gps_lat          DOUBLE,
  userid           text,
  notes            text,
  numValue         DECIMAL(11,3),
  txtValue         text,
  PRIMARY KEY(node_id, traitInstance_id, timestamp),
  FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE,
  FOREIGN KEY(traitInstance_id) REFERENCES traitInstance(id) ON DELETE CASCADE
);

create table deviceName(
  androidId  CHAR(16) PRIMARY KEY,
  nickName   VARCHAR(63)
);

