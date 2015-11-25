--
-- SQL statements to create system tables for FieldPrime.
-- NB, assumes database is created and used.
-- We could add logging tables in here perhaps.
-- -----------------------------------------------------------------------------------------------------

create database fpsys;
use fpsys;

create table user(
  id          int primary key auto_increment,
  login	      varchar(63) not null,
  name        varchar(255),
  passhash    varchar(255),
  login_type  int,
  permissions int default 0,
  UNIQUE (login)
);

create table project(
  id     int primary key auto_increment,
  name   varchar(255) unique,
  dbname varchar(63),
  unique (name)
);

create table userProject(
  user_id      int,
  project_id   int,
  permissions  int default 0,
  unique (user_id, project_id),
  foreign key(user_id) references user(id) on delete cascade,
  foreign key(project_id) references project(id) on delete cascade on update cascade
);

