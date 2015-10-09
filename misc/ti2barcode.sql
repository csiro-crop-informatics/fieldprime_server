# given txt values for each node spread across tis 5 and 7, bring them into node:barcode
# trial id is 9
update node n
set barcode = (select txtValue from datum where node_id=n.id and traitInstance_id in (5,7)) 
where n.trial_id = 9;


