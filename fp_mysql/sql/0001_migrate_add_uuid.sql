BEGIN;
--
-- Add field uuid to node
--
ALTER TABLE `node` ADD COLUMN `uuid` varchar(64) NULL UNIQUE;
--
-- Add field uuid to project
--
ALTER TABLE `project` ADD COLUMN `uuid` varchar(64) NULL UNIQUE;
--
-- Add field uuid to trait
--
ALTER TABLE `trait` ADD COLUMN `uuid` varchar(64) NULL UNIQUE;
--
-- Add field uuid to trial
--
ALTER TABLE `trial` ADD COLUMN `uuid` varchar(64) NULL UNIQUE;
COMMIT;

