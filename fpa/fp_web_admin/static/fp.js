
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

// delme
function old_addRow(){
    var currval = document.getElementById('catCount').value;
    var root = document.getElementById('catTable');
    var allRows = root.getElementsByTagName('tr');    //the rows' collection 
    var cRow = allRows[1].cloneNode(true)             //the clone of the 1st row 
    var cInp = cRow.getElementsByTagName('input');    //the inputs' collection of the 1st row 
    for(var i=0; i<cInp.length; i++){                 //changes the inputs' names (indexes the names) 
        var name = cInp[i].getAttribute('name')
        var nameStub = name.substring(0, name.length - 1)
        cInp[i].setAttribute('name', nameStub + currval) 
        cInp[i].setAttribute('id', nameStub + currval) 
    } 
    var btn=document.createElement("BUTTON");
    var t=document.createTextNode("-");
    btn.appendChild(t);
    btn.setAttribute('onclick', "if (this.getAttribute(\'id\') !== \'zap_0\') this.parentNode.parentNode.removeChild(this.parentNode)");
    cRow.appendChild(btn);


    root.appendChild(cRow);                           //appends the cloned row as a new row
    document.getElementById('catCount').value = ++currval;
} 
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
    btn.setAttribute('onclick', "if (this.getAttribute(\'id\') !== \'zap_0\') this.parentNode.parentNode.removeChild(this.parentNode)");
    row.appendChild(btn);

    document.getElementById('catCount').value = ++currval;
} 

/*
 * CategoryTraitFormElement()
 * Display table for category entry, users can add or delete rows.
 */
function CategoryTraitFormElement(newDivId) {
    html = "<fieldset><legend>Categories:</legend>";
    html += '<table id="catTable" width="766"  border="0" cellspacing="0" cellpadding="0">';
    html += '<input type="hidden" id="catCount" name="catCount" value="1" />';            // hidden row counter, note may be gaps in the count
    html += '<tr><td>Caption</td><td>Value</td><td>Image File</td>' +                     // Table headers
        '<td><input name="button" type="button" value="+" onclick="addRow()"</td></tr>';  // new row button
    html += '<tr>' +
        '<td width="191"><input type="text" id="caption_0" name="caption_0" /></td>' +
        '<td width="191"><input type="text" id="value_0" name="value_0" /></td>' +
        '<td width="191"><input type="file" id="imgfile_0" name="imgfile_0"/></td>' +
        //'<td width="286"><input name="button" id="zap_0" type="button" value="-"' +
        //'onclick="this.parentNode.parentNode.removeChild(this.parentNode.parentNode)"></td>' +
        //'onclick="if (this.getAttribute(\'id\') !== \'zap_0\') this.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode)"></td>' +
        //'onclick="alert(this.getAttribute(\'id\'))"></td>' +
        '</tr></table>';

    html += "</fieldset>";
    return html;
}


/*
 * SetTraitFormElements()
 * Called on select of trait type on new trait form.
 * Modifies the form to reflect the selected trait type.
 */
function SetTraitFormElements(divName, tType){
    var newDivId = 'traitTypeSpecificFields';
    var parentDiv = document.getElementById(divName);

    // Remove previously created elements:
    var prevAdded = document.getElementById(newDivId);
    if (prevAdded != null) parentDiv.removeChild(prevAdded);

    // Create new element with id:
    var newdiv = document.createElement('div');
    newdiv.id = newDivId;
    switch(tType) {
    case "0": // integer
    case "1": // decimal
        // Min and Max:
        html = "<p>Minimum: <input type='text' name='min'><p>Maximum: <input type='text' name='max'><br>";

        // Validation:
        html += '<p>Validation, score should be:';
        html += '<select name="validationOp">';
        html += '<option value="0">Greater Than</option>';
        html += '<option value="0">Less Than</option>';
        html += '</select>'
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    case "2": // string
        break;
    case "3": // categorical, we need to add elements for adding categories: <value>,<caption>,[<image>]
        html = CategoryTraitFormElement(newDivId);
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    case "4": // date
        break;
    }
}

function ValidateTraitForm()
{
    var cap = document.getElementById("cap_id").value;
    if (cap == null || cap == "") {
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
            if (catCap != null && catCap == "") {
                alert("Please provide a caption for row " + i);
                return false;
            }
            var catVal  = document.getElementById("value_" + i).value;
            if (catVal != null && catVal == "") {
                alert("Please provide a value for row " + i);
                return false;
            }
        }
    }
}