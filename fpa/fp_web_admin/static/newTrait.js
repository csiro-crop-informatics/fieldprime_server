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


fpTrait._addRow = function(rootDiv, preset, isNew) {
    if (isNew)
        preset = {caption:"", value:"", imageURL:"None"};
    var tab = rootDiv.catTable;
    var drow = tab.insertRow(-1);
    var index = rootDiv.catCount;

    // Caption:
    var capcell = drow.insertCell(-1);
    var capInput = document.createElement('input');
    capInput.type = 'text';
    capInput.id = 'caption_' + index;
    capInput.name = capInput.id;
    capInput.value = preset.caption;
    capcell.appendChild(capInput);

    // Value field:
    var val = document.createElement("input");
    val.type = "text";
    val.id = 'value_' + index;
    val.value = preset.value;
    val.name = 'value_' + index;
    val.readOnly = !isNew;
    drow.insertCell(-1).appendChild(val);

    // Image URL:
    var icel = drow.insertCell(-1);
    if (preset.imageURL === 'None') {
        icel.appendChild(document.createTextNode("\u00A0No Image\u00A0"));  // \u00A0
    } else {
        var anc = document.createElement("A");
        anc.href = preset.imageURL;
        anc.appendChild(document.createTextNode('\u00A0Image set\u00A0'));
        icel.appendChild(anc);
    }
    icel = drow.insertCell(-1);
    var fcel = document.createElement("input");
    fcel.type = 'file';
    fcel.id = 'imgfile_' + index;
    fcel.name = 'imgfile_' + index;
    fcel.style.display = 'inline';
    icel.appendChild(fcel);

    // New cell needs delete button:
    if (isNew && index > 0) {
        var btn=document.createElement("BUTTON");
        btn.appendChild(document.createTextNode("-"));
        btn.onclick = function() {
            btn.parentNode.parentNode.removeChild(btn.parentNode);
            --rootDiv.catCount;
        };
        drow.appendChild(btn);
    }
    ++rootDiv.catCount;
};

/*
 * categoryTraitFormElement()
 * Adds to rootDiv a fieldset containing table of category trait elements.
 * presets are existing values to put in the table.
 */
fpTrait.categoryTraitFormElement = function(rootDiv, presets) {
    var fset = rootDiv.appendChild(fpTrait.createFieldset('Categories'));
    var tab = fset.appendChild(document.createElement('table'));
    tab.id = "catTable";
    tab.style.border="0";

    // Table header:
    var hrow = tab.createTHead().insertRow(-1);
    hrow.insertCell(-1).innerHTML = "Caption";
    hrow.insertCell(-1).innerHTML = "Value";
    hrow.insertCell(-1).appendChild(document.createTextNode("Image"));
    hrow.insertCell(-1).appendChild(document.createTextNode(""));
    var btn = document.createElement("BUTTON");
    btn.name = "button";
    btn.innerHTML = "+";
    btn.onclick = function(){
        fpTrait._addRow(rootDiv, null, true);
        return false;  // need this else browser leaves the page
    };
    btn.topDiv = rootDiv;
    hrow.insertCell(-1).appendChild(btn);

    // Store the count and the table in the div, for access by other functions:
    rootDiv.catCount = 0;  //(presets !== undefined) ? presets.length : 1;
    rootDiv.catTable = tab;

    // Table contents:
    if (presets !== undefined) {
        // add rows for existing categories (with no remove button):
        for (var i = 0; i < presets.length; i++) {
            fpTrait._addRow(rootDiv, presets[i], false);
        }
    } else {
        fpTrait._addRow(rootDiv, null, true);
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
                alert("Please provide a caption for row " + (i + 1));
                return false;
            }
            var catVal  = document.getElementById("value_" + i).value;
            if (catVal !== null && catVal === "") {
                alert("Please provide a value for row " + (i+1));
                return false;
            }
        }
        break;
    }
    return true;
};
