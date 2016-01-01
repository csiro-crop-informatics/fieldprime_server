grant all on *.* to Superadm@localhost identified by 'foo' with grant option;
grant all on *.* to fpwserver@'%' identified by 'bar';
flush privileges;
use fpsys
insert user (login,name,passhash,login_type,permissions) values ('mk','m k', '***REMOVED***', 3, 1);
insert userProject values (1,1,1);

