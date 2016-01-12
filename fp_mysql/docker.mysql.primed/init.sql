# init.sql
# Michael Kirk   2016
#
# Initial run time setup of fieldprime mysql container.
# 
# Todo parameterize passwords for fpwserver and fieldprime user.
# 

# Create fpsys database:
source /fieldprime/fpsys.sql

# Setup fpwserver user:
grant all on *.* to fpwserver@'%' identified by 'bar';
flush privileges;

#
# Create default FieldPrime project database:
#
set @DB_NAME='fp_main';
set @PROJ_NAME='main';
set @CONTACT_NAME='Michael Kirk';
set @CONTACT_EMAIL='***REMOVED***';
create database if not exists fp_main;
use fp_main;
source /fieldprime/fprime.create.tables.sql;
insert fpsys.project (name, dbname) values (@PROJ_NAME, database());
insert project (id, up_id, name, contactName, contactEmail)
  values ((select id from fpsys.project where name=@PROJ_NAME),
  null, @PROJ_NAME, @CONTACT_NAME, @CONTACT_EMAIL);
insert system (name, value) values ('contactName', @CONTACT_NAME), ('contactEmail', @CONTACT_EMAIL);

#
# Create user mk with access to default project:
#
use fpsys
insert user (login,name,passhash,login_type,permissions) values ('mk','m k',
  '***REMOVED***',
  3, 1);
insert userProject values (1,1,1);

