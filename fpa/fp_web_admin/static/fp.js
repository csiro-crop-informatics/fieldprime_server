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
function addRow(r){
    var currval = document.getElementById('myHiddenField').value;
    var root = r.parentNode;//the root 
    var allRows = root.getElementsByTagName('tr');//the rows' collection 
    var cRow = allRows[1].cloneNode(true)//the clone of the 1st row 
    var cInp = cRow.getElementsByTagName('input');//the inputs' collection of the 1st row 
    for(var i=0;i<cInp.length;i++){//changes the inputs' names (indexes the names) 
        var name = cInp[i].getAttribute('name')
        var nameStub = name.substring(0, name.length - 1)
        cInp[i].setAttribute('name', nameStub + (allRows.length)) 
    } 
    //for(var i=0;i<cInp.length;i++){//changes the inputs' names (indexes the names) 
    //    cInp[i].setAttribute('name',cInp[i].getAttribute('name')+'_'+(allRows.length+1)) 
    //} 
    root.appendChild(cRow);//appends the cloned row as a new row
    document.getElementById('myHiddenField').value = ++currval;
} 
function removeCat(r){
    var currval = document.getElementById('myHiddenField').value;
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
    document.getElementById('myHiddenField').value = ++currval;
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
        html = "<fieldset><legend>Categories:</legend>";

        /*
        html += '<input type="hiddden" name="numCats" id="numCats" value="1" />'
        html += "<button type='button' name='addcat' value='HTML' onclick='AddCategory(" + newDivId + ")'>Add Category</button>";
        html += "<div id='catList'>"
        html += "<p>Caption:<input type='text' name='caption'>";
        html += "Value: <input type='text' name='catval'>";
        //html += "<button name='addcat' value='HTML' onclick='AddCategory(" + newDivId + ")'>Add Category</button>";
        //html += "<button name='addcat' type='submit' value='HTML' onclick='testjs(\"hallo\")'>HTML</button>";
        //html += "<input type='button' value='Add another category' onclick='AddCategory()'"
        html += "</div>"
        */

html += 'Category entry not yet supported, please contact Webmaster to create categories'
/*
        html += '<table id="catTable" width="766"  border="0" cellspacing="0" cellpadding="0"> \
                 <input type="hiddden" name="myHiddenField" id="myHiddenField" value="1" /> \
                  <tr><td>Caption</td><td>Value</td> \
                      <td><input name="button" type="button" value="+" onclick="addRow(this.parentNode.parentNode)"</td> \
                  </tr> \
                  <tr> \
                   <td width="191"><input type="text" name="caption_0" /></td> \
                   <td width="191"><input type="text" name="value_0" /></td> \
                   <td width="286"><input name="button" type="button" value="-" \
                       onclick="this.parentNode.parentNode.removeChild(this.parentNode.parentNode)"></td> \
                 </tr> \
                 </table>'
*/
 //                  <td width="286"><input name="button" type="button" value="-" onclick="removeCat(this.parentNode.parentNode)"></td> \


        html += "</fieldset>"
        newdiv.innerHTML = html;
        parentDiv.appendChild(newdiv);
        break;
    case "4": // date
        break;
    }
}
