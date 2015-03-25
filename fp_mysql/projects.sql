create table project(
  id           int primary key auto_increment,
  up_id        int,
  name         varchar(63) unique not null,
  contactName  text,
  contactEmail text,
  foreign key (up_id) references project(id)
);

insert into project (id, up_id) values (2, null);
update project set name = (select substring(database(), 4));
update project set contactName = (select value from system where name = 'contactName');
update project set contactEmail = (select value from system where name = 'contactEmail');
alter table trial add column project_id int;
alter table trial add constraint foreign key (project_id) references project(id);
update trial set project_id = 2;

alter table trait add column project_id int default NULL;
alter table trait add constraint foreign key (project_id) references project(id);
update trait set project_id = 2 where sysType = 1;

alter table trait add column trial_id int default NULL;
alter table trait add constraint foreign key (trial_id) references trial(id);
update trait t set trial_id = (select trial_id from trialTrait where trait_id = t.id) where sysType != 1;

alter table trait drop column sysType;

alter table trait change type datatype int
