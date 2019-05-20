-- MySQL dump 10.13  Distrib 5.7.26, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: fieldprime_all_api
-- ------------------------------------------------------
-- Server version	5.7.10

create database fieldprime;
use fieldprime;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attributeValue`
--

DROP TABLE IF EXISTS `attributeValue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `attributeValue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value` longtext NOT NULL,
  `node_id` int(11) NOT NULL,
  `nodeAttribute_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `attributeValue_nodeAttribute_id_node_id_ac389da4_uniq` (`nodeAttribute_id`,`node_id`),
  KEY `attributeValue_node_id_307d46f2_fk_node_id` (`node_id`),
  CONSTRAINT `attributeValue_nodeAttribute_id_34a7157e_fk_nodeAttribute_id` FOREIGN KEY (`nodeAttribute_id`) REFERENCES `nodeAttribute` (`id`),
  CONSTRAINT `attributeValue_node_id_307d46f2_fk_node_id` FOREIGN KEY (`node_id`) REFERENCES `node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datum`
--

DROP TABLE IF EXISTS `datum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datum` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userid` longtext,
  `timestamp` bigint(20) NOT NULL,
  `gps_long` double DEFAULT NULL,
  `gps_lat` double DEFAULT NULL,
  `notes` longtext,
  `numValue` decimal(11,3) DEFAULT NULL,
  `txtValue` longtext,
  `node_id` int(11) NOT NULL,
  `traitInstance_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `datum_node_id_traitInstance_id_timestamp_bdddfb45_uniq` (`node_id`,`traitInstance_id`,`timestamp`),
  KEY `datum_traitInstance_id_9f56818e_fk_traitInstance_id` (`traitInstance_id`),
  CONSTRAINT `datum_node_id_1ae6633b_fk_node_id` FOREIGN KEY (`node_id`) REFERENCES `node` (`id`),
  CONSTRAINT `datum_traitInstance_id_9f56818e_fk_traitInstance_id` FOREIGN KEY (`traitInstance_id`) REFERENCES `traitInstance` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `deviceName`
--

DROP TABLE IF EXISTS `deviceName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deviceName` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `androidId` varchar(16) NOT NULL,
  `nickName` varchar(63) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpapi_projectpermissions`
--

DROP TABLE IF EXISTS `fpapi_projectpermissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpapi_projectpermissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `dbname` varchar(255) DEFAULT NULL,
  `old_dbname` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `node`
--

DROP TABLE IF EXISTS `node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `node` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `row` int(11) NOT NULL,
  `col` int(11) NOT NULL,
  `description` longtext,
  `barcode` longtext,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `old_node_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `trial_id` int(11) NOT NULL,
  `uuid` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `node_project_id_f0455bcf_fk_project_id` (`project_id`),
  KEY `node_trial_id_54542b55_fk_trial_id` (`trial_id`),
  CONSTRAINT `node_project_id_f0455bcf_fk_project_id` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
  CONSTRAINT `node_trial_id_54542b55_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nodeAttribute`
--

DROP TABLE IF EXISTS `nodeAttribute`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nodeAttribute` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(127) NOT NULL,
  `datatype` int(11) NOT NULL,
  `func` int(11) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nodeAttribute_trial_id_name_1490cd9e_uniq` (`trial_id`,`name`),
  CONSTRAINT `nodeAttribute_trial_id_e22359cc_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nodeNote`
--

DROP TABLE IF EXISTS `nodeNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nodeNote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `note` longtext,
  `timestamp` bigint(20) NOT NULL,
  `userid` longtext,
  `node_id` int(11) NOT NULL,
  `token_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `nodeNote_node_id_a5c30416_fk_node_id` (`node_id`),
  KEY `nodeNote_token_id_ac4ee7a3_fk_token_id` (`token_id`),
  CONSTRAINT `nodeNote_node_id_a5c30416_fk_node_id` FOREIGN KEY (`node_id`) REFERENCES `node` (`id`),
  CONSTRAINT `nodeNote_token_id_ac4ee7a3_fk_token_id` FOREIGN KEY (`token_id`) REFERENCES `token` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(63) NOT NULL,
  `contactName` longtext NOT NULL,
  `contactEmail` longtext NOT NULL,
  `old_project_db` varchar(63) DEFAULT NULL,
  `up_id` int(11) DEFAULT NULL,
  `uuid` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `project_up_id_573428ee_fk_project_id` (`up_id`),
  CONSTRAINT `project_up_id_573428ee_fk_project_id` FOREIGN KEY (`up_id`) REFERENCES `project` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system`
--

DROP TABLE IF EXISTS `system`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(63) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `token`
--

DROP TABLE IF EXISTS `token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `token` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(31) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `token_trial_id_06159e29_fk_trial_id` (`trial_id`),
  CONSTRAINT `token_trial_id_06159e29_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tokenNode`
--

DROP TABLE IF EXISTS `tokenNode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tokenNode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `localId` int(11) NOT NULL,
  `node_id` int(11) NOT NULL,
  `token_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tokenNode_token_id_localId_1834b570_uniq` (`token_id`,`localId`),
  KEY `tokenNode_node_id_4897cef0_fk_node_id` (`node_id`),
  CONSTRAINT `tokenNode_node_id_4897cef0_fk_node_id` FOREIGN KEY (`node_id`) REFERENCES `node` (`id`),
  CONSTRAINT `tokenNode_token_id_b1440870_fk_token_id` FOREIGN KEY (`token_id`) REFERENCES `token` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trait`
--

DROP TABLE IF EXISTS `trait`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trait` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trial_id` int(11) DEFAULT NULL,
  `caption` varchar(63) NOT NULL,
  `description` longtext NOT NULL,
  `datatype` int(11) NOT NULL,
  `tid` longtext,
  `unit` longtext,
  `min` decimal(10,0) DEFAULT NULL,
  `max` decimal(10,0) DEFAULT NULL,
  `old_trait_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `uuid` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `trait_project_id_538c3948_fk_project_id` (`project_id`),
  CONSTRAINT `trait_project_id_538c3948_fk_project_id` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traitCategory`
--

DROP TABLE IF EXISTS `traitCategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `traitCategory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value` int(11) NOT NULL,
  `caption` longtext NOT NULL,
  `imageURL` longtext,
  `trait_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `traitCategory_trait_id_value_976adf41_uniq` (`trait_id`,`value`),
  CONSTRAINT `traitCategory_trait_id_acd4b82c_fk_trait_id` FOREIGN KEY (`trait_id`) REFERENCES `trait` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traitInstance`
--

DROP TABLE IF EXISTS `traitInstance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `traitInstance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dayCreated` int(11) NOT NULL,
  `seqNum` int(11) NOT NULL,
  `sampleNum` int(11) NOT NULL,
  `token_id` int(11) NOT NULL,
  `trait_id` int(11) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `traitInstance_trial_id_trait_id_token__0febffb3_uniq` (`trial_id`,`trait_id`,`token_id`,`seqNum`,`sampleNum`),
  KEY `traitInstance_token_id_2e91ed59_fk_token_id` (`token_id`),
  KEY `traitInstance_trait_id_b8792e82_fk_trait_id` (`trait_id`),
  CONSTRAINT `traitInstance_token_id_2e91ed59_fk_token_id` FOREIGN KEY (`token_id`) REFERENCES `token` (`id`),
  CONSTRAINT `traitInstance_trait_id_b8792e82_fk_trait_id` FOREIGN KEY (`trait_id`) REFERENCES `trait` (`id`),
  CONSTRAINT `traitInstance_trial_id_881c8b51_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traitString`
--

DROP TABLE IF EXISTS `traitString`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `traitString` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pattern` longtext,
  `trait_id` int(11) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `traitString_trial_id_trait_id_8eedef87_uniq` (`trial_id`,`trait_id`),
  KEY `traitString_trait_id_18e6ab8e_fk_trait_id` (`trait_id`),
  CONSTRAINT `traitString_trait_id_18e6ab8e_fk_trait_id` FOREIGN KEY (`trait_id`) REFERENCES `trait` (`id`),
  CONSTRAINT `traitString_trial_id_1eca04d9_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trial`
--

DROP TABLE IF EXISTS `trial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trial` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(63) NOT NULL,
  `site` longtext,
  `year` longtext,
  `acronym` longtext,
  `old_trial_id` int(11) DEFAULT NULL,
  `project_id` int(11) NOT NULL,
  `uuid` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `trial_project_id_01136278_fk_project_id` (`project_id`),
  CONSTRAINT `trial_project_id_01136278_fk_project_id` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trialProperty`
--

DROP TABLE IF EXISTS `trialProperty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trialProperty` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(63) NOT NULL,
  `value` longtext,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `trialProperty_trial_id_name_2feebf91_uniq` (`trial_id`,`name`),
  CONSTRAINT `trialProperty_trial_id_bd5a9186_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trialTrait`
--

DROP TABLE IF EXISTS `trialTrait`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trialTrait` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `barcodeAtt_id` int(11) DEFAULT NULL,
  `trait_id` int(11) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `trialTrait_trait_id_trial_id_df086775_uniq` (`trait_id`,`trial_id`),
  KEY `trialTrait_barcodeAtt_id_319d47eb_fk_nodeAttribute_id` (`barcodeAtt_id`),
  KEY `trialTrait_trial_id_7095aef4_fk_trial_id` (`trial_id`),
  CONSTRAINT `trialTrait_barcodeAtt_id_319d47eb_fk_nodeAttribute_id` FOREIGN KEY (`barcodeAtt_id`) REFERENCES `nodeAttribute` (`id`),
  CONSTRAINT `trialTrait_trait_id_2da2d943_fk_trait_id` FOREIGN KEY (`trait_id`) REFERENCES `trait` (`id`),
  CONSTRAINT `trialTrait_trial_id_7095aef4_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trialTraitNumeric`
--

DROP TABLE IF EXISTS `trialTraitNumeric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trialTraitNumeric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `min` decimal(18,9) DEFAULT NULL,
  `max` decimal(18,9) DEFAULT NULL,
  `validation` longtext,
  `trait_id` int(11) NOT NULL,
  `trial_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `trialTraitNumeric_trial_id_trait_id_c6dcabc5_uniq` (`trial_id`,`trait_id`),
  KEY `trialTraitNumeric_trait_id_c2d511d1_fk_trait_id` (`trait_id`),
  CONSTRAINT `trialTraitNumeric_trait_id_c2d511d1_fk_trait_id` FOREIGN KEY (`trait_id`) REFERENCES `trait` (`id`),
  CONSTRAINT `trialTraitNumeric_trial_id_cb6a0924_fk_trial_id` FOREIGN KEY (`trial_id`) REFERENCES `trial` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `login` varchar(63) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `passhash` varchar(255) DEFAULT NULL,
  `login_type` int(11) DEFAULT NULL,
  `permissions` int(11) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `login` (`login`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `userProject`
--

DROP TABLE IF EXISTS `userProject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userProject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `permissions` int(11) DEFAULT NULL,
  `project_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userProject_user_id_project_id_0aed86a1_uniq` (`user_id`,`project_id`),
  KEY `userProject_project_id_fc5f812c_fk_fpapi_projectpermissions_id` (`project_id`),
  CONSTRAINT `userProject_project_id_fc5f812c_fk_fpapi_projectpermissions_id` FOREIGN KEY (`project_id`) REFERENCES `fpapi_projectpermissions` (`id`),
  CONSTRAINT `userProject_user_id_e2d5def6_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_groups`
--

DROP TABLE IF EXISTS `user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_groups_user_id_group_id_40beef00_uniq` (`user_id`,`group_id`),
  KEY `user_groups_group_id_b76f8aba_fk_auth_group_id` (`group_id`),
  CONSTRAINT `user_groups_group_id_b76f8aba_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_groups_user_id_abaea130_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_user_permissions`
--

DROP TABLE IF EXISTS `user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_user_permissions_user_id_permission_id_7dc6e2e0_uniq` (`user_id`,`permission_id`),
  KEY `user_user_permission_permission_id_9deb68a3_fk_auth_perm` (`permission_id`),
  CONSTRAINT `user_user_permission_permission_id_9deb68a3_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_user_permissions_user_id_ed4a47ea_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-20 13:11:46
