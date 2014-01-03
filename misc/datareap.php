<?php
// datareap.php
// Michael Kirk 2013
// Original php version of datareap (now FieldPrime) server.
// No longer used.


//### GLOBALS: ###################################################################

// Database table and field names:

// Table trialUnit:
$TBL_TRIALUNIT = "trialUnit";
$TU_ID = "id";
$TU_TID = "trial_id";
$TU_ROW = "row";
$TU_COL = "col";
$TU_DESC = "description";
$TU_BARCODE = "barcode";
$TU_FIELDS = array($TU_ID, $TU_TID, $TU_ROW, $TU_COL, $TU_DESC, $TU_BARCODE);

// Table trial:
$TBL_TRIAL = "trial";
$T_ID = "id";

// Table trialTrait:
$TBL_TRIALTRAIT = "trialTrait";
$TT_TRIALID = "trial_id";
$TT_TRAITID = "trait_id";

// Table trait:
$TBL_TRAIT = "trait";
$TR_ID = "id";
$TR_TYPE = "type";
$TR_CAP = "caption";
$TR_DES = "description";
$TR_SYSTYPE = "sysType";
$TR_MIN = "min";
$TR_MAX = "max";
$SYSTYPE_ADHOC = 2;

// Table traitInstance:
$TBL_TI = "traitInstance";
$TI_ID = "id";
$TI_TID = "trial_id";
$TI_TRAIT_ID = "trait_id";
$TI_DC = "dayCreated";
$TI_SEQNUM = "seqNum";
$TI_SAMPNUM = "sampleNum";
$TI_TOKEN = "token";

// Table trialUnitAttribute
$TBL_TUA = "trialUnitAttribute";
$TUA_ID = "id";
$TUA_NAME = "name";
$TUA_TID = "trial_id";

// Table attributeValues
$TBL_ATTVALS = "attributeValues";
$AV_TUA_ID = "trialUnitAttribute_id";
$AV_TU_ID = "trialUnit_id";
$AV_VAL = "value";

// Table traitCategory:
$TBL_TCAT = "traitCategory";
$TC_TRAIT_ID = "trait_id";
$TC_VALUE = "value";
$TC_CAPTION = "caption";
$TC_IMAGE = "imageURL";

// Trait Types:
$T_INTEGER = 0;
$T_DECIMAL = 1;
$T_STRING = 2;
$T_CATEGORICAL = 3;

// Table datum names:
$TBL_DATUM = "datum";
$DM_ID = "id";
$DM_TRAITINSTANCE_ID = "traitInstance_id";
$DM_TRIALUNIT_ID = "trialUnit_id";
$DM_TIMESTAMP = "timestamp";
$DM_GPS_LONG = "gps_long";
$DM_GPS_LAT = "gps_lat";
$DM_USERID = "userid";
$DM_VALUE = "value";
$DM_NOTES = "notes";

// Table system:
$TBL_SYSTEM = "system";
$SYS_KEY = "name";
$SYS_VAL = "value";


// Debug switch:
$gdbg = 0;

//### FUNCTIONS: ###################################################################

/*
 * DBConnect()
 * NB Exits script with JSON error message on failure.
 */
function DBConnect($user = '', $password = '')
{
  global $TBL_SYSTEM;
  global $SYS_KEY;
  global $SYS_VAL;

  $dbname = 'fp_' . $user;
  $mysqli = new mysqli('localhost', 'fpwserver', "fpws_g00d10ch", $dbname);
  if (mysqli_connect_errno()) {
    printf("Connect failed: %s\n", mysqli_connect_error());
    exit();
  }

  // Check password:
  $qry = "SELECT $SYS_VAL FROM $TBL_SYSTEM where $SYS_KEY = 'appPassword'";
  $res = $mysqli->query($qry) or die("gt1:".$mysqli->error.__LINE__);
  if ($res->num_rows > 0) {
     if ($rec = $res->fetch_assoc()) {
         if ($rec[$SYS_VAL] == $password) {
             return $mysqli;
         }
     }
     ExitJsonError("Password failure for database $user");
  }

  // No password configured, so carry on:
  return $mysqli;
}

/*
 * ExitJsonError()
 * Exit with JSON error object.
 */
function ExitJsonError($errMsg)
{
  $ret = array();
  $ret["error"] = $errMsg;
  echo json_encode($ret);
  exit();
}


/*
 * AbortDBerr()
 * Exit program with error message.
 * Suggested usage is to call with $tag set to something identify the
 * code causing the problem, $dbhandle must be an open db connection,
 * and $linenum should be __LINE__
 * For production environment, the db error should probably not be included.
 */
function AbortDBerr($tag, $dbhandle, $linenum)
{
  exit("$tag:$linenum:" . $dbhandle->error);
}

function GetTrialList($suser, $spassword)
{
  global $TBL_TRIAL;
  $hd = $suser ? DBConnect($suser, $spassword) : DBConnect();
  $res = $hd->query("SELECT * FROM $TBL_TRIAL") or AbortDBerr("gtl1", $hd, __LINE__);
  $trials = array();
  while ($rec = $res->fetch_assoc()) {
    $trials[] = $rec;
  }
  $hd->close();
  return array("trials" => $trials);
}


/*
 * GetTraitsArray()
 * Returns associative array representing the traits for the specified trial.
 * Note ad hoc traits are not returned.
 */
function GetTraitsArray($hd, $trialID)
{
  global $T_CATEGORICAL;
  global $TBL_TRIALTRAIT;
  global $TT_TRAITID;
  global $TT_TRIALID;
  global $TBL_TRAIT;
  global $TR_SYSTYPE;
  global $TBL_TCAT;
  global $TC_TRAIT_ID;
  global $SYSTYPE_ADHOC;

  $res = $hd->query("SELECT $TBL_TRAIT.* FROM $TBL_TRAIT, $TBL_TRIALTRAIT where $TT_TRAITID = id " .
                    //"and $TT_TRIALID = $trialID")
                    "and $TT_TRIALID = $trialID and $TR_SYSTYPE != $SYSTYPE_ADHOC")
    or AbortDBerr("gta1", $hd, __LINE__);
  $traits = array();
  while ($rec = $res->fetch_assoc()) {
    if ($rec["type"] == $T_CATEGORICAL) {
      $arCats = array();
      $cats = $hd->query("SELECT * FROM $TBL_TCAT where $TC_TRAIT_ID = $rec[id]") or AbortDBerr("gta2", $hd, __LINE__);
      while ($cat = $cats->fetch_assoc()) {
      	$arCats[] = $cat;
      }
      $rec["categories"] = $arCats;
    }
    $traits[] = $rec;
  }
  return $traits;
}


/*
 * GetTrialAttributesArray()
 * Returns array of attribute names for specified trial.
 */
function GetTrialAttributesArray($hd, $trialID)
{
  global $TUA_NAME;
  global $TBL_TUA;
  global $TUA_TID;

  $res = $hd->query("select $TUA_NAME from $TBL_TUA where $TUA_TID = $trialID") or die("gtaa1:".$hd->error.__LINE__);
  $tuaNames = array();
  while ($rec = $res->fetch_assoc()) {
    $tuaNames[] = $rec[$TUA_NAME];
  }
  return $tuaNames;
}


/*
 * GetTrialUnitsArray()
 *
 */
function GetTrialUnitsArray($hd, $trialID)
{
  global $TU_FIELDS;
  global $TBL_TUA;
  global $TUA_ID;
  global $TUA_NAME;

  global $TBL_TRIALUNIT;
  global $TU_TID;
  global $TU_ID;

  global $TBL_ATTVALS;
  global $AV_VAL;
  global $AV_TU_ID;
  global $AV_TUA_ID;

  $res = $hd->query("SELECT * FROM $TBL_TRIALUNIT where $TU_TID = $trialID") or die("gtua1:".$hd->error.__LINE__);
  $trialUnits = array();
  while ($rec = $res->fetch_assoc()) {
    $tu = array();
    foreach ($TU_FIELDS as $field) {
      $tu[$field] = $rec[$field];
    }

    // Get the attributes:
    $tuid = $rec[$TU_ID];
    $qry = "SELECT $TUA_NAME, $AV_VAL FROM $TBL_ATTVALS join $TBL_TUA on $TUA_ID = $AV_TUA_ID " .
      "where $AV_TU_ID = $tuid";
    $atts = $hd->query($qry) or die("gtua2:".$qry." ".$hd->error.__LINE__);
    while ($att = $atts->fetch_assoc()) {
      $tu[$att[$TUA_NAME]] = $att[$AV_VAL];
    }

    $trialUnits[] = $tu;
  }
  return $trialUnits;
}


/*
 * GetTrial()
 *
 */
function GetTrial($id, $andid, $suser, $spassword)
{
  global $TBL_TRIAL;
  global $TR_ID;

  $hd = $suser ? DBConnect($suser, $spassword) : DBConnect();
  $topArray = array();

  // Get trial attributes:
  $qry = "SELECT * FROM $TBL_TRIAL where $TR_ID = $id";
  $res = $hd->query($qry) or die("gt1:".$hd->error.__LINE__);
  if ($rec = $res->fetch_assoc()) {
    $topArray = $rec;
  }

  // Use the android device ID postfixed with the current time in seconds as the serverTrialId.
  // This should ensure different tokens for the same trial being downloaded multiple times on
  // a single device (with delete in between), as long as they are not created within the same
  // second (and this is not an expected use case):
  $topArray["serverToken"] = $andid . "." . time();

  // Get the attributes:
  $topArray["attributes"] = GetTrialAttributesArray($hd, $id);

  // Get the trial units:
  $topArray["trialUnits"] = GetTrialUnitsArray($hd, $id);
 
  // Get the traits associated with this trial:
  $topArray["traits"] = GetTraitsArray($hd, $id);;
 
  $hd->close();
  return $topArray;
}

/*
 * CreateAdHocTrait()
 *
 */
function CreateAdHocTrait($suser, $spassword, $caption, $description, $type, $min, $max)
{
  global $TBL_TRAIT;
  global $TR_ID;
  global $TR_TYPE;
  global $TR_CAP;
  global $TR_DES;
  global $TR_SYSTYPE;
  global $TR_MIN;
  global $TR_MAX;
  global $SYSTYPE_ADHOC;

  $hd = $suser ? DBConnect($suser, $spassword) : DBConnect();
  $qry = "INSERT INTO $TBL_TRAIT ($TR_TYPE, $TR_CAP, $TR_DES, $TR_SYSTYPE, $TR_MIN, $TR_MAX) " . 
	"VALUES ($type, '$caption', '$description', $SYSTYPE_ADHOC, $min, $max)";
  //if ($gdbg) echo "QUERY: $qry\n";
  //$res = $hd->query($qry) or ExitJsonError("ERROR (sCAHT):" . $qry);
  $res = $hd->query($qry) or ExitJsonError("ERROR (sCAHT):" . $hd->error);
  $new_trait_id = $hd->insert_id;
  $ret = array();
  $ret['traitId'] = $new_trait_id;
  return $ret;
}


/*
 * ProcessTrialUpload()
 * Takes uploaded trial data (decoded JSON) and update database as appropriate.
 *
 */
function ProcessTrialUpload($data, $suser, $password)
{
  global $gdbg;
  global $TBL_TRAIT;
  global $TR_ID;
  global $TR_TYPE;
  global $TBL_DATUM;
  global $DM_ID;
  global $DM_TRAITINSTANCE_ID;
  global $DM_TRIALUNIT_ID;
  global $DM_TIMESTAMP;
  global $DM_GPS_LONG;
  global $DM_GPS_LAT;
  global $DM_USERID;
  global $DM_VALUE;
  global $DM_NOTES;
  global $TBL_TI;
  global $TI_ID;
  global $TI_TID;
  global $TI_TRAIT_ID;
  global $TI_DC;
  global $TI_SEQNUM;
  global $TI_SAMPNUM;
  global $TI_TOKEN;

  $hd = $suser ? DBConnect($suser, $password) : DBConnect();
  $trial = $data["serverId"];
  $token = $data["serverToken"];

  // Process the traitInstances:
  $aTIs = $data["traitInstances"];
  foreach ($aTIs as $ti) {
    $traitID = $ti["trait_id"];
    $dayCreated = $ti["dayCreated"];
    $seqNum = $ti["seqNum"];
    $sampNo = $ti["sampleNum"];
    $aData = $ti["data"];
    // Lookup the trait type:
    $qry = "SELECT $TR_TYPE from $TBL_TRAIT where $TR_ID = $traitID";
    $res = $hd->query($qry) or AbortDBerr("ptu1", $hd, __LINE__);
    $rec = $res->fetch_assoc() or AbortDBerr("ptu1.5:$qry", $hd, __LINE__);
    $type = $rec["type"];

    /*
     * Retrieve or Create traitInstance record:
     * Note how trait instances from different devices are handled
     * Trait instances are uniquely identified by trial/trait/seqNum/sampleNum and token.
     */
    $qry = "SELECT $TI_ID FROM $TBL_TI WHERE $TI_TID = $trial AND  $TI_TRAIT_ID = $traitID " .
      "AND $TI_SEQNUM = $seqNum AND $TI_SAMPNUM = $sampNo and $TI_TOKEN = '$token'";
    ($res = $hd->query($qry)) or AbortDBerr("ptu2", $hd, __LINE__);
    $rowCount = $res->num_rows;

    if ($rowCount == 1) { // Trait instance already exist, use it:
      $rec = $res->fetch_assoc() or AbortDBerr("ptu3", $hd, __LINE__);
      $ti_id = $rec[$TI_ID];
    } else if ($rowCount == 0) { // Trait instance doesn't already exist, create one:
       $qry = "INSERT INTO $TBL_TI ($TI_TID, $TI_TRAIT_ID, $TI_DC, $TI_SEQNUM, $TI_SAMPNUM, $TI_TOKEN) " . 
	"VALUES ($trial, $traitID, $dayCreated, $seqNum, $sampNo, '$token')";
      if ($gdbg) echo "QUERY: $qry\n";
      $res = $hd->query($qry) or AbortDBerr("ptu4", $hd, __LINE__);
      $ti_id = $hd->insert_id;
    } else {
      die("bad row count $rowCount");
    }

    // Do things needed to reflect the type of this trait instance (which affects which field the value is stored in).
    // MFK Need type objects!
    if ($type == 2 || $type == 5) {
      $valueField = "txtValue";
      $valueTypeCode = "s";
    } else {
      $valueField = "numValue";
      $valueTypeCode = "d";
    }

    /*
     * Process the datum(s):
     * Note we need to avoid re-adding data that has already been uploaded.
     * This is achieved because Datum has a primary index on trialUnit_id + traitInstance_id + timestamp,
     * so duplicates will not be inserted (the "INSERT IGNORE" skips the resulting error triggered).
     */
    $stmt = $hd->prepare("INSERT IGNORE INTO $TBL_DATUM ($DM_TRIALUNIT_ID, $DM_TRAITINSTANCE_ID, $DM_TIMESTAMP, " .
			 "$DM_GPS_LONG, $DM_GPS_LAT, $DM_USERID, $DM_NOTES, $valueField) VALUES (?,?,?,?,?,?,?,?)")
      or AbortDBerr("ptu5", $hd, __LINE__);
    $stmt->bind_param('iiiddss' . $valueTypeCode, $tuid, $ti_id, $timestamp, $gps_long, $gps_lat, $userid, $notes, $value)
      or AbortDBerr("ptu6", $hd, __LINE__);
    foreach ($aData as $aDatum) {
      $tuid = $aDatum[$DM_TRIALUNIT_ID];
      $timestamp = $aDatum[$DM_TIMESTAMP];
      $gps_long = $aDatum[$DM_GPS_LONG];
      $gps_lat = $aDatum[$DM_GPS_LAT];
      $userid = $aDatum[$DM_USERID];
      $notes = $aDatum[$DM_NOTES];
      if (array_key_exists($DM_VALUE, $aDatum))
	$value = $aDatum[$DM_VALUE];
      else $value = null;

      // Check if this datum already present ?

      $stmt->execute() or AbortDBerr("ptu7", $hd, __LINE__);
    }
    $stmt->close();
  }

  $hd->close();
  return "Success";
}



//### MAIN: ####################################################################################

/*
 * Deal with the POST case:
 * Client has uploaded data, process it and exit.
 */
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  //$suser = $_POST['suser'];

  $data = file_get_contents('php://input');
  $json = json_decode($data, true);
  $suser = $json["suser"];
  $password = $json["apppw"];
  if (is_null($json)) 
    exit("Data upload failed, cannot parse the JSON");
  if ($gdbg) echo (var_dump($json));
  exit(ProcessTrialUpload($json, $suser, $password));
}



// Prevent caching.
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 01 Jan 1996 00:00:00 GMT');

// The JSON standard MIME header.
header('Content-type: application/json');

/*
 * Deal with the GET case:
 * Client wants something, specified via 'cmd' parameter
 */
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
  $cmd = $_GET['cmd'];
  $suser = $_GET['suser'];
  $spassword = $_GET['pw'];
  switch ($cmd) {
  case "list_trials":
    $data = GetTrialList($suser, $spassword);
    break;
  case "get_trial":
    $id = $_GET['id'];
    $andid = $_GET['andid'];   // not used yet, but could be logged, or used to limit access to recognized devices
    $data = GetTrial($id, $andid, $suser, $spassword);
    break;
  case "create_adhoc":
    $data = CreateAdHocTrait($suser, $spassword, $_GET['caption'], $_GET['description'],
                             $_GET['type'], $_GET['min'], $_GET['max']);
    break;
  default:
    exit("Unknown command specified");
  }

  // Send the data.
  echo json_encode($data);
}

?>

