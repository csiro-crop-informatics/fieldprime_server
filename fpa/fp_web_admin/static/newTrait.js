/*
 * addRow()
 * Add row to catTable.
 */
function addRow(){
    var currval = document.getElementById('catCount').value;
    var root = document.getElementById('catTable');
    var row=root.insertRow(-1);
    var names = ['caption_', 'value_', 'imgfile_'];
    for (var i = 0; i < names.length; i++) {
        var cap = document.createElement("input");
        cap.type = (i == 2) ? "file" : "text";
        cap.id = names[i] + currval;
        cap.name = cap.id;
        var cell=row.insertCell(-1);
        cell.appendChild(cap);
    }
    // Add delete button, could put it in cell, but doesn't seem to be necessary
    var btn=document.createElement("BUTTON");
    var t=document.createTextNode("-");
    btn.appendChild(t);
    btn.setAttribute('onclick', "removeRow(this)");
    row.appendChild(btn);

    document.getElementById('catCount').value = ++currval;
}

/*
 * removeRow()
 * Remove row from catTable.
 */
function removeRow(btn) {
    btn.parentNode.parentNode.removeChild(btn.parentNode);
    var currval = document.getElementById('catCount').value;
    document.getElementById('catCount').value = --currval;
}

/*
 * CategoryTraitFormElement()
 * Returns html table for category entry, users can add or delete rows.
 */
function CategoryTraitFormElement(newDivId, presets) {
    var html = "<fieldset><legend>Categories:</legend>";
    html += '<table id="catTable" width="766"  border="0" cellspacing="0" cellpadding="0">';
    html += '<input type="hidden" id="catCount" name="catCount" value="1" />';            // hidden row counter, note may be gaps in the count
    html += '<tr><td>Caption</td><td>Value</td><td>Image File</td>' +                     // Table headers
        '<td><input name="button" type="button" value="+" onclick="addRow()"</td></tr>';  // new row button
    if (presets !== undefined) {
        for (var i = 0; i < presets.length; i++) {
            html += '<tr>' +                                                                      // add first row (no remove button)
                '<td width="191"><input type="text" id="caption_0" value="' + presets[i].caption + '" name="caption_0" /></td>' +
                '<td width="191"><input type="text" id="value_0" name="value_0" /></td>' +
                '<td width="191"><input type="file" id="imgfile_0" name="imgfile_0"/></td>' +
                '</tr>';

    /*
    if (curVals !== undefined) {
        alert('yes curvals');
        var arrayLength = curVals.length;
        for (var i = 0; i < arrayLength; i++) {
           alert(curVals[i].caption);
        }
    }
*/



        }
    } else {
        html += '<tr>' +                                                                      // add first row (no remove button)
            '<td width="191"><input type="text" id="caption_0" name="caption_0" /></td>' +
            '<td width="191"><input type="text" id="value_0" name="value_0" /></td>' +
            '<td width="191"><input type="file" id="imgfile_0" name="imgfile_0"/></td>' +
            '</tr>';
    }
    html += '</table>';

    html += "</fieldset>";
    return html;
}

/*
 * SetTraitFormElements()
 * Called on select of trait type on newTrait form.
 * Modifies the form to reflect the selected trait type.
 * Creates and adds a new div with fields specific to traitType.
 * Param divName should be the id of the element to which
 * the new fields should be added.
 */
function SetTraitFormElements(divName, traitType, curVals){
/*
    if (curVals !== undefined) {
        alert('yes curvals');
        var arrayLength = curVals.length;
        for (var i = 0; i < arrayLength; i++) {
           alert(curVals[i].caption);
        }
    }
*/
    var newDivId = 'SpecificFields';
    var parentDiv = document.getElementById(divName);

    // Remove previously created elements, if present:
    var prevAdded = document.getElementById(newDivId);
    if (prevAdded !== null) parentDiv.removeChild(prevAdded);

    // Create new element with id:
    var newdiv = document.createElement('div');
    newdiv.id = newDivId;
    switch(traitType) {
    case "2": // string
        break;
    case "4": // date
        break;
    case "0": // integer
    case "1": // decimal
        break;
        // type specific stuff here incomplete, should be the same as the Validation button in the traits table
        // Min and Max:
        html = "<p>Minimum: <input type='text' name='min'><p>Maximum: <input type='text' name='max'><br>";

        // Validation:
        html += '<p>Validation, score should be:';
        html += '<select name="validationOp">';
        html += '<option value="0">Greater Than</option>';
        html += '<option value="0">Less Than</option>';
        html += '</select>';
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    case "3": // categorical, we need to add elements for adding categories: <value>,<caption>,[<image>]
        var html = CategoryTraitFormElement(newDivId, curVals);
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    }
}

/*
 * ValidateTraitForm()
 * validation function for new trait form.
 */
function ValidateTraitForm()
{
    var cap;
    try {
        cap = document.getElementById("cap_id").value;
    } catch (e) {
        alert("Unexpected error validating trait.");
        return false;
    }
    if (cap === null || cap === "") {
        alert("Please provide a caption");
        return false;
    }
    var selVal = document.getElementById("traitType").value;
    if (selVal < 0) {
        alert("Please select a trait type");
        return false;
    }
    // If category trait, check categories:
    switch (selVal) {
    case "3":
        var catCount = document.getElementById("catCount").value;
        for (var i=0; i < parseInt(catCount); i++) {
            var catCap = document.getElementById("caption_" + i).value;
            if (catCap !== null && catCap === "") {
                alert("Please provide a caption for row " + i);
                return false;
            }
            var catVal  = document.getElementById("value_" + i).value;
            if (catVal !== null && catVal === "") {
                alert("Please provide a value for row " + i);
                return false;
            }
        }
    }
}


/* Not used ****************************************************************************
var counter = 1;
var limit = 3;

function addInput(divName){
     if (counter == limit)  {
          alert("You have reached the limit of adding " + counter + " inputs");
     }
     else {
          var newdiv = document.createElement('div');
          newdiv.innerHTML = "Entry " + (counter + 1) + " <br><input type='text' name='myInputs[]'>";
          document.getElementById(divName).appendChild(newdiv);
          counter++;
     }
}

function testjs(msg){
    alert(msg)
}

function AddCategory(divId) {
    alert(divId.id);
}

function removeCat(r){
    var currval = document.getElementById('catCount').value;
    var root = r.parentNode;//the root
    var allRows = root.getElementsByTagName('tr');//the rows' collection
    var cRow = allRows[1].cloneNode(true)//the clone of the 1st row
    var cInp = cRow.getElementsByTagName('input');//the inputs' collection of the 1st row
    for(var i=0;i<cInp.length;i++){//changes the inputs' names (indexes the names)
        var name = cInp[i].getAttribute('name')
        var nameStub = name.substring(0, name.length - 1)
        cInp[i].setAttribute('name', nameStub + (allRows.length+1))
    }
    root.appendChild(cRow);//appends the cloned row as a new row
    document.getElementById('catCount').value = ++currval;
}

*/
