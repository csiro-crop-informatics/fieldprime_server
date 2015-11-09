 /*
  * fpTrait object - functions for make trait page.
  *
  *
  */

/*global $:false,alert:false,d3:false*/

var fpTrait = {};

/*
 * These two should prob be in less specific library..
 */
fpTrait.isValidDecimal = function(inputtxt) {
    var decPat =  /^[+-]?[0-9]+(?:\.[0-9]+)?$/g;
    return inputtxt.match(decPat);
};
fpTrait.createFieldset = function(legendText) {
    var fieldset = document.createElement('fieldset');
    var legend = fieldset.appendChild(document.createElement("legend"));
    legend.appendChild( document.createTextNode(legendText));
    return fieldset;
};


/*
 * _addRow()
 * Add row to catTable.
 */
fpTrait._addRow = function(){
    var rootDiv = this.topDiv;
    var row=rootDiv.catTable.insertRow(-1);

    // Add caption, value, and imageFile fields:
    var names = ['caption_', 'value_', 'imgfile_'];
    for (var i = 0; i < names.length; i++) {
        var cap = document.createElement("input");
        cap.type = (i == 2) ? "file" : "text";
        cap.id = names[i] + rootDiv.catCount;
        cap.name = cap.id;
        row.insertCell(-1).appendChild(cap);
    }

    // Add delete button, could put it in cell, but doesn't seem to be necessary
    var btn=document.createElement("BUTTON");
    btn.appendChild(document.createTextNode("-"));
    btn.onclick = function() {
        btn.parentNode.parentNode.removeChild(btn.parentNode);
        --rootDiv.catCount;
    };
    row.appendChild(btn);

    ++rootDiv.catCount;
    return false;  // need this else browser leaves the page
};

/*
 * categoryTraitFormElement()
 * Adds to newDiv a fieldset containing table of category trait elements.
 * presets are existing values to put in the table.
 */
fpTrait.categoryTraitFormElement = function(newDiv, presets) {
    var fset = newDiv.appendChild(fpTrait.createFieldset('Categories'));
    var tab = fset.appendChild(document.createElement('table'));
    tab.style.width = "766";
    tab.style.padding = "0";
    tab.id = "catTable";
    tab.style.border="0";

    // Store the count and the table in the div, for access by other functions:
    newDiv.catCount = (presets !== undefined) ? presets.length : 1;
    newDiv.catTable = tab;

    // Table header:
    var hrow = tab.createTHead().insertRow(-1);
    hrow.insertCell(-1).innerHTML = "Caption";   // use document.createTextNode("Caption");
    hrow.insertCell(-1).innerHTML = "Value";
    hrow.insertCell(-1).appendChild(document.createTextNode("Image File"));
    if (true) {
        var btn = document.createElement("BUTTON");
        btn.name = "button";
        btn.innerHTML = "+";
        btn.onclick = fpTrait._addRow;
        btn.topDiv = newDiv;
        hrow.insertCell(-1).appendChild(btn);
    } else {
        hrow.insertCell(-1).innerHTML = '<input name="button" type="button" value="+" onclick="fpTrait._addRow()">';
    }

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
};

/*
 * setTraitFormElements()
 * Called on select of trait type on newTrait form.
 * Modifies the form to reflect the selected trait type.
 * Creates and adds a new div with fields specific to traitType.
 * Param divName should be the id of the element to which
 * the new fields should be added.
 */
fpTrait.setTraitFormElements = function(divName, traitType, curVals){
    var rootDiv = document.getElementById(divName);
    rootDiv.innerHTML = ''; // Remove previously created elements, if present:
    switch(traitType) {
    case "2": // string
    case "4": // date
    case "0": // integer
    case "1": // decimal
        /*
         * NB when called from new trait form, there is no type specific fields for these
         * types - since it may be a system trait. We should perhaps detect this..
         */
        break;
    case "3": // categorical, we need to add elements for adding categories: <value>,<caption>,[<image>]
        fpTrait.categoryTraitFormElement(rootDiv, curVals);
        break;
    }
};

/*
 * validateNewTraitForm()
 * Checks the form fields that are only present on the new trait form,
 * and then calls func to check field on new and existing trait forms.
 */
fpTrait.validateNewTraitForm = function(divName)
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

    return fpTrait.validateTraitTypeSpecific(divName, selVal);
};

/*
 * validateTraitTypeSpecific()
 * validation function for type specific fields of trait form.
 */
fpTrait.validateTraitTypeSpecific = function(divName, traitType)
{
    switch (traitType) {
    case "2": // string
    case "4": // date
    case "0": // integer
    case "1": // decimal
        /*
         * NB there may or may not be type specific fields, when we are
         * called from the new trait form there will be nothing (attow).
         * So we must be careful to allow this. See comment in setTraitFormElements.
         */
        break;
    case "3":
        // If category trait, check categories:
        var rootDiv = document.getElementById(divName);
        for (var i=0; i < parseInt(rootDiv.catCount, 10); i++) {
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
        break;
    }
    return true;
};
