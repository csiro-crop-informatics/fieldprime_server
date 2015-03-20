use fpsys;

create table project(
  id     int primary key auto_increment,
  name   varchar(255),
  dbname varchar(63),
  unique (name)
);

insert into project (name, dbname) select project, concat("fp_", project) from userProject group by project;
update userProject set project_id = (select id from project where name = project);
alter table userProject drop foreign key userProject_ibfk_1;
alter table userProject drop index user_id;
alter table userProject add constraint foreign key (user_id) references user(id) on delete cascade;
alter table userProject drop column project;
alter table userProject add constraint foreign key (project_id) references project(id) on delete cascade;
alter table userProject add constraint unique user_project (user_id, project_id);



use fp_mk;
create table project(
  id           int primary key auto_increment,
  up_id        int,
  name         varchar(63) unique not null,
  contactName  text,
  contactEmail text,
  foreign key (up_id) references project(id)
);

insert into project (up_id) values (null);
update project set name = (select substring(database(), 4));
update project set contactName = (select value from system where name = 'contactName');
update project set contactEmail = (select value from system where name = 'contactEmail');
alter table trial add column project_id int;
alter table trial add constraint foreign key (project_id) references project(id);
update trial set project_id = 1;

