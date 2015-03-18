--
-- SQL statements to create system tables for FieldPrime.
-- NB, assumes database is created and used.
-- We could add logging tables in here perhaps.
-- -----------------------------------------------------------------------------------------------------


create table user(
  id       INT PRIMARY KEY AUTO_INCREMENT,
  login	   VARCHAR(63) not null,
  name     VARCHAR(255),
  UNIQUE (login)
);

create table userProject(
  user_id      int,
  dbname       varchar(63),
  project      VARCHAR(63) not null,
  permissions  int default 0,
  UNIQUE (user_id, project),
  FOREIGN KEY(user_id) references user(id) on delete cascade
);




