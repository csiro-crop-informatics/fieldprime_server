# handy.sql
# Michael Kirk 2014
#
# Various bits of sql that have been used to get information out of,
# or modify the FieldPrime databases. Some of it just one-offs, that
# may be useful to modify for tasks in the future.
#
# NB, some of these, perhaps, should be made available in each database
# by default as a stored procdure. Or this file could be cleaned up and
# modified so that it creates a set of useful functions, and then this
# file could be pasted into the mysql command line as needed to make the
# functions available.
#

# dryland heading date:
SELECT row, col, numValue as HeadingDate from datum d, trialUnit u, traitInstance t
WHERE d.traitInstance_id = t.id and d.trialUnit_id = u.id
and u.trial_id = 3 and t.trait_id = 10
and d.traitInstance_id > 28
INTO OUTFILE '/tmp/dryland_headDate.csv'
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

# irrigated heading date:
SELECT row, col, numValue as HeadingDate from datum d, trialUnit u, traitInstance t
WHERE d.traitInstance_id = t.id and d.trialUnit_id = u.id
and u.trial_id = 2 and t.trait_id = 10
and d.traitInstance_id > 28
INTO OUTFILE '/tmp/irrigated_headDate.csv'
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

# dryland zadoks:
SELECT row, col, numValue as HeadingDate from datum d, trialUnit u, traitInstance t
WHERE d.traitInstance_id = t.id and d.trialUnit_id = u.id
and u.trial_id = 3 and t.trait_id = 9
and d.traitInstance_id > 28
INTO OUTFILE '/tmp/dryland_zadoks.csv'
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

# irrigated zadoks:
SELECT row, col, numValue as HeadingDate from datum d, trialUnit u, traitInstance t
WHERE d.traitInstance_id = t.id and d.trialUnit_id = u.id
and u.trial_id = 2 and t.trait_id = 9
and d.traitInstance_id > 28
INTO OUTFILE '/tmp/irrigated_zadoks.csv'
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

### USEFUL TO SEE DATA: ###################################################################
# Get datum count for each traitInstance with extra info:
#
select traitInstance_id, l.name, token, caption, dayCreated, count(*) from datum d, traitInstance t, trait r, trial l
where d.traitInstance_id = t.id and t.trait_id = r.id and t.trial_id = l.id
group by traitInstance_id order by l.name, caption, dayCreated, token
;

######################################################################
# Find trial units with missing scores from set of trait instances
#
set @TID = 3;
set @TILIST = '36,38';
select row, col, trial_id from trialUnit
where trial_id = @TID and id not in
(select trialUnit_id from datum where FIND_IN_SET(traitInstance_id, @TILIST) > 0)
;


######################################################################
# Change row number in datum table for given row in traitInstance:
#
select count(*) from datum d1, datum d2, trialUnit t1, trialUnit t2
where d1.traitInstance_id = 36 and d2.traitInstance_id = 36
and d1.trialUnit_id = t1.id and d2.trialUnit_id = t2.id
and t1.row = 8
;

select t1.row, t1.col, t1.id, t2.row, t2.col, t2.id, t1.id - t2.id from datum d1, trialUnit t1, trialUnit t2
where d1.traitInstance_id = 36
and d1.trialUnit_id = t1.id
and t2.trial_id = t1.trial_id
and t1.row = 8 and t2.row = 6
and t1.col = t2.col
;

select count(*) from datum d1, trialUnit t1, trialUnit t2
where d1.traitInstance_id = 36
and d1.trialUnit_id = t1.id
and t2.trial_id = t1.trial_id
and t1.row = 8 and t2.row = 6
and t1.col = t2.col
and t1.id - t2.id != 96
;

update datum, trialUnit t set trialUnit_id = trialUnit_id - 96
where datum.trialUnit_id = t.id and traitInstance_id = 36 and row = 8 

select row, count(*) from datum d, trialUnit t, traitInstance i
where d.trialUnit_id = t.id
and d.traitInstance_id = i.id
and t.trial_id = 3
and i.trait_id = 9
group by row;


select row, col, z.numValue, h.numValue from datum z, datum h, trialUnit t
where z.trialUnit_id = t.id and h.trialUnit_id = t.id

select count(*) from (datum z, trialUnit t, traitInstance iz, traitInstance ih) left join datum h
on z.trialUnit_id = t.id and h.trialUnit_id = t.id
and t.trial_id = 3
and z.traitInstance_id = iz.id and h.traitInstance_id = ih.id
and iz.trait_id = 9 and ih.trait_id = 10
;

select row, col, numValue from datum z, trialUnit t, traitInstance iz
where z.trialUnit_id = t.id
and t.trial_id = 3
and z.traitInstance_id = iz.id
and iz.trait_id = 9 
;


#
# Find trial units with missing scores.
#


select trialUnit_id from datum where traitInstance_id = 66 and trialUnit_id not in
(select trialUnit_id from datum where traitInstance_id = 67);


#
# Heading date as attribute values
# concat('first', 'second')

insert ignore into attributeValues (trialUnitAttribute_id, trialUnit_id, value)
select 54, trialUnit_id, concat(substring(CAST(numValue AS CHAR),7,2),'/',substring(CAST(numValue AS CHAR),5,2))
from datum where traitInstance_id in (37,39,65,67)
and numValue is not null;
 
select count(*) from datum where traitInstance_id in (57,59,70);
select count(*) from datum where traitInstance_id in (30,35,61,63);
select count(*) from datum where traitInstance_id in (37,39,65,67);

select count(*) from datum where traitInstance_id in (57,59,70) and numValue is not null group by trialUnit_id having count(*) > 1;
select count(*) from datum where traitInstance_id in (30,35,61,63) and numValue is not null group by trialUnit_id having count(*) > 1;
select count(*) from datum where traitInstance_id in (37,39,65,67) and numValue is not null group by trialUnit_id having count(*) > 1;

select count(*), min(numValue), max(numValue) from datum where traitInstance_id in (57,59,70) and numValue is not null group by trialUnit_id having count(*) > 1 and min(numValue) != max(numValue);
select count(*), min(numValue), max(numValue) from datum where traitInstance_id in (30,35,61,63) and numValue is not null group by trialUnit_id having count(*) > 1 and min(numValue) != max(numValue);
select count(*), min(numValue), max(numValue) from datum where traitInstance_id in (37,39,65,67) and numValue is not null group by trialUnit_id having count(*) > 1 and min(numValue) != max(numValue);


tua_id  trial  tis
52      1      57,59,70
53      2      30,35,61,63
54      3      37,39,65,67


--
-- Construct Latest Zadoks attribute
--
-- Create trialUnitAttribute record, eg:
insert trialUnitAttribute (trial_id,name) values (<trialId>,'Last Zadoks');
-- store the id of new trialUnitAttribute
set @TUA = 70;

insert ignore into attributeValues (trialUnitAttribute_id, trialUnit_id, value)
select @TUA, trialUnit_id, CAST(numValue AS CHAR)
from datum where traitInstance_id in (96,101,104,105)
and numValue is not null;

insert ignore into attributeValues (trialUnitAttribute_id, trialUnit_id, value)
select @TUA, trialUnit_id, "NA"
from datum where traitInstance_id in (96,101,104,105)
and numValue is null;

insert ignore into attributeValues (trialUnitAttribute_id, trialUnit_id, value)
select 69, trialUnit_id, "NA"
from datum where traitInstance_id in (97,102,103)
and numValue is null;

select traitInstance_id, l.name, token, caption, dayCreated, count(*) from datum d, traitInstance t, trait r, trial l
where d.traitInstance_id = t.id and t.trait_id = r.id and t.trial_id = l.id and (t.trial_id in (12,13))
group by traitInstance_id order by l.name, caption, dayCreated, token
;


### Generate Latest Score attribute:
set @trial = 1;
set @trait = 2;
set @n = 0;
select max(timestamp), @N := @N +1 AS rank from datum d, traitInstance ti
where d.traitInstance_id = ti.id and ti.trial_id = @trial and ti.trait_id = @trait
group by d.trialUnit_id
;

