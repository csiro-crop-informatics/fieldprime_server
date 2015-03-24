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
update trial set project_id = 2;

alter table trait add column project_id int;
alter table trait add constraint foreign key (project_id) references project(id);
update trait set project_id = 2 where sysType = 1;


alter table trait change type datatype int