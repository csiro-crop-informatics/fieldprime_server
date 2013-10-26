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
    alert(divId);
}

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
        newdiv.innerHTML = "<p>Minimum: <input type='text' name='min'><p>Maximum: <input type='text' name='max'><br>";
        parentDiv.appendChild(newdiv);
        break;
    case "2": // string
        break;
    case "3": // categorical, we need to add elements for adding categories: <value>,<caption>,[<image>]
        html = "<p>Categories:";
        html += "<p>Caption:<input type='text' name='caption'>";
        html += "Value: <input type='text' name='catval'>";
        html += "<button name='addcat' value='HTML' onclick='AddCategory(\"" + newDivId + "\")'>Add Category</button>";
        //html += "<button name='addcat' type='submit' value='HTML' onclick='testjs(\"hallo\")'>HTML</button>";
        html += "<input type='button' value='Add another category' onclick='AddCategory()'"
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    case "4": // date
        break;
    }
}
