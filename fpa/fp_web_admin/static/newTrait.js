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



function createFieldset(legendText) {
    var fieldset = document.createElement('fieldset');
    var legend = fieldset.appendChild(document.createElement("legend"));
    legend.appendChild( document.createTextNode(legendText));
    return fieldset;
}


/*
 * CategoryTraitFormElement()
 * Adds to newDiv a fieldset containing table of category trait elements.
 * presets are existing values to put in the table.
 * MFK: this version of the function an attempt to use only the dom, no html.
 */
function CategoryTraitFormElement(newDiv, presets) {
    var fset = newDiv.appendChild(createFieldset('Categories'));
    var tab = fset.appendChild(document.createElement('table'));
    tab.style.width = "766";
    tab.style.padding = "0";
    tab.id = "catTable";
    tab.style.border="0";

    // Add hidden field that records count:
    var hiddenCount = fset.appendChild(document.createElement("input"));
    hiddenCount.type = "hidden";
    hiddenCount.id = "catCount";
    hiddenCount.value = (presets !== undefined) ? presets.length : 1;  // hidden row counter, note may be gaps in the count

    // Table header:
    //MFK - why do the data rows end up in the table header?
    var hrow = tab.createTHead().insertRow(-1);
    hrow.insertCell(-1).innerHTML = "Caption";
    hrow.insertCell(-1).innerHTML = "Value";
    hrow.insertCell(-1).appendChild(document.createTextNode("Image File"));
    hrow.insertCell(-1).innerHTML = '<input name="button" type="button" value="+" onclick="addRow()">';

    // Table contents:
    var drow;
    var dcell;
    var inp;
    if (presets !== undefined) {
        // add rows for existing categories (with no remove button):
        for (var i = 0; i < presets.length; i++) {
            drow = tab.insertRow(-1);

            // Caption:
            var capcell = drow.insertCell(-1);
            capcell.style.width = '191';
            //capcell.innerHTML = '<input type="text" id="caption_' + i + '" value="'
            // + presets[i].caption + '" name="caption_' + i + '"/>';
            var capInput = document.createElement('input');
            capInput.type = 'text';
            capInput.id = 'caption_' + i;
            capInput.name = capInput.id;
            capInput.value = presets[i].caption;
            capcell.appendChild(capInput);

            // Value field:
            var val = document.createElement("input");
            val.type = "text";
            val.id = 'value_' + i;
            val.value = presets[i].value;
            val.name = 'value_' + i;
            val.readOnly = true;
            drow.insertCell(-1).appendChild(val);

            // Image URL:
            var icel = drow.insertCell(-1);
            icel.style.width = '191';
            icel.style.whiteSpace = 'nowrap';
            if (presets[i].imageURL === 'None') {
                icel.appendChild(document.createTextNode("No Image"));
            } else {
                var anc = document.createElement("A");
                anc.href = presets[i].imageURL;
                anc.appendChild(document.createTextNode('Image set'));
                icel.appendChild(anc);
            }
            var fcel = document.createElement("input");
            fcel.type = 'file';
            fcel.id = 'imgfile_' + i;
            fcel.name = 'imgfile_' + i;
            icel.appendChild(fcel);
/* This an attempt to stop the two elements (text node and file input) in this td from wrapping, unsuccessful so far..
            // Image URL:
            var icel = drow.insertCell(-1);
            icel.style.width = '191';
            icel.style.whiteSpace = 'nowrap';
            icel.style.display = 'inline-block';
            var bdiv = document.createElement("div");
            bdiv.style.display = 'inline';
            bdiv.style.whiteSpace = 'nowrap';
            //bdiv.style.overflow = 'scroll';
            if (presets[i].imageURL === 'None') {
                bdiv.appendChild(document.createTextNode("No Image"));
            } else {
                var anc = document.createElement("A");
                anc.href = presets[i].imageURL;
                anc.appendChild(document.createTextNode('Image set'));
                bdiv.appendChild(anc);
            }
            var fcel = document.createElement("input");
            fcel.type = 'file';
            fcel.id = 'imgfile_' + i;
            fcel.name = 'imgfile_' + i;
            bdiv.appendChild(fcel);
            icel.appendChild(bdiv);
*/
        }
    } else {
        // Set up single initial row:
        drow = tab.insertRow(-1);

        // Caption:
        dcell = drow.insertCell(-1);
        dcell.style.width = '191';
        inp = document.createElement('input');
        inp.type = 'text';
        inp.id = 'caption_0';
        inp.name = inp.id;
        dcell.appendChild(inp);

        // Value field:
        inp = document.createElement("input");
        inp.type = "text";
        inp.id = 'value_0';
        inp.name = inp.id;
        drow.insertCell(-1).appendChild(inp);

        // Image URL:
        inp = document.createElement("input");
        inp.type = "file";
        inp.id = 'imgfile_0';
        inp.name = inp.id;
        drow.insertCell(-1).appendChild(inp);
    }
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
/*
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
*/
    case "3": // categorical, we need to add elements for adding categories: <value>,<caption>,[<image>]
        CategoryTraitFormElement(newdiv, curVals);
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
        window.alert("Unexpected error validating trait.");
        return false;
    }
    if (cap === null || cap === "") {
        window.alert("Please provide a caption");
        return false;
    }
    var selVal = document.getElementById("traitType").value;
    if (selVal < 0) {
        window.alert("Please select a trait type");
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
