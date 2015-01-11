/*
 * Create fplib object: A single global variable to hold all the
 * bits and pieces we need access to globally. In a single object
 * so as not to pollute the global namespace too much.
 */
var fplib = {};


/*
 * initTabs()
 * parameter tabListId should be the id of a UL element containing links
 * for the desired tabs. Each LI should be an anchor for the relevant div
 * on the page.
 * Note all the styling is done in this function. There is no separate css
 * required.
 */
fplib.initTabs = function (tabListId) {
    var tabLinks = {};
    var contentDivs = {};
    var STORAGE_TAG = "fpCurrTrialPageTab";
    var background_color = "#022C38";
    var color = "#fff";
    var selected_background_color = "#f00";
    var selected_color = "#fff";

    function setTab(tabId) {
      // store tabId in session storage for retrieval on navigation back to page:
      if (window.sessionStorage){
        sessionStorage.setItem(STORAGE_TAG, tabId);
      }

      // Highlight the selected tab, and dim all others.
      // Also show the selected content div, and hide all others.
      for (var id in contentDivs) {
        if (id == tabId) {
          //tabLinks[id].className = 'selected';
          contentDivs[id].style.display = "";

        } else {
          //tabLinks[id].className = '';
          contentDivs[id].style.display = "none";
        }
        styleTabLink(tabLinks[id], id === tabId);
      }

    }

    function showTab() {
      var selectedId = getHash(this.getAttribute('href'));
      setTab(selectedId);
      return false;  // to stop the browser following the link
    }

    function getFirstChildWithTagName(element, tagName) {
      for (var i = 0; i < element.childNodes.length; i++ ) {
        if (element.childNodes[i].nodeName === tagName) return element.childNodes[i];
      }
    }

    function getHash(url) {
      var hashPos = url.lastIndexOf('#');
      return url.substring(hashPos + 1);
    }

    function styleTabLink(tabLink, selected) {
        tabLink.style.fontWeight = selected ? 'bold' : '';
        tabLink.style.color = selected ? selected_color : color;
        tabLink.style.backgroundColor = selected ? selected_background_color : background_color;
        tabLink.style.padding = selected ? '20px 10px 10px' : '10px';
        tabLink.style.minWidth = '120px';
        tabLink.style.display = 'block';
        tabLink.style.border = '1px solid #c9c3ba';
        tabLink.style.borderRadius = '5px 5px 0 0';
        tabLink.style.borderBottom = 'none';
        tabLink.style.textDecoration = 'none';
        tabLink.style.margin = '0';
    }

    //-- Code: ------------------------------------------------------
    var i;
    var id;

    // Get the tab list element and style it:
    var tabListElement = document.getElementById(tabListId);
    tabListElement.style.listStyleType = 'none';
    tabListElement.style.whiteSpace = 'nowrap';
    tabListElement.style.margin = '30px 0 0 0';
    tabListElement.style.padding = '0';

    // Process the children:
    var tabListItems = tabListElement.childNodes;
    for (i = 0; i < tabListItems.length; i++ ) {
      if (tabListItems[i].nodeName == "LI") {
        // style the li:
        tabListItems[i].style.display = 'inline-block';
        tabListItems[i].style.margin = '0';

        var tabLink = getFirstChildWithTagName(tabListItems[i], 'A');
        id = getHash(tabLink.getAttribute('href'));
        tabLinks[id] = tabLink;
        styleTabLink(tabLink, false);

        // Record and style the content chunk:
        var contChunk = document.getElementById(id);
        contentDivs[id] = contChunk;
        contChunk.style.border = "1px solid #c9c3ba";
        contChunk.style.padding = "0.5em";

      }
    }

    // Assign onclick events to the tab links, and
    var focusFunc = function() { this.blur(); };
    for (id in tabLinks) {
      tabLinks[id].onclick = showTab;
      tabLinks[id].onfocus = focusFunc;
    }

    var currTab;
    if (window.sessionStorage) {
      currTab=sessionStorage.getItem(STORAGE_TAG);
      fplib.currTab = currTab;
    }
    setTab(currTab);
};


fplib.extrasSubmit = function(event) {
    var url = event.data.url;
    if (false) { // put validation here if required
        alert("Insertion Failed Some Fields are Blank....!!");
    } else {
        // Construct object contain the form fields:
        var ffob = {};
        var fels = document.getElementById("extras").elements;

        for (var i = 0; i < fels.length; i++) {
            var el = fels[i];
            if (el.type === "radio") {  // We only want selected value of radio button set
                if (el.checked) {
                    ffob[el.name] = el.value;
                    //alert(el.name + ":" + el.value + ":" + el.type);
                }
            }
            else {
                ffob[el.name] = el.value;
                //alert(el.name + ":" + el.value + ":" + el.type);
            }
        }

        // Returns successful data submission message when the entered information is stored in database.
        $.post(url, ffob,
            function(data, textStatus) {
                alert(data);
                //alert(textStatus);   // should we check this is "success"?
                //$('#form')[0].reset(); // To reset form fields - what's this?
            },
            "html"
        );

    }
    return false;
};

fplib.msg = function (msg) {
    alert(msg);
}

/*
 * setDirty()
 * Set dirty attribute goUp levels from el.
 */
fplib.setDirty = function (el, goUp) {
    for (var i=0; i<goUp; ++i) {
        el = el.parentNode;
    }
    el.setAttribute("data-dirty", "y");
};

/*
 * userAdd
 * Adds row to user table, with user to fill in the login and permissions.
 */
fplib.userAdd = function () {
    var utab = document.getElementById('userTable');
    fplib.addUserTableRow(utab, true);
};


/*
 * userSaveChanges
 * Send user details to server with ajax.
 * Users are in table with id userTable, rows for new users
 * are identified by having attribute "data-addedUser" (see
 * function userAdd).
 */
fplib.userSaveChanges = function (destUrl) {
    var updateUsers = {};
    var newUsers = {};
    var delUsers = {};
    // get the users and encode them in json
    var table = document.getElementById("userTable");

    var sfunc = function(data) {
        fplib.msg(JSON.stringify(data.errors));
        fplib.fillUserTable(destUrl)();
    };

    for (var i = 1, row; row = table.rows[i]; i++) {
       if (row.hasAttribute("data-addedUser")) {
           var loginId = row.cells[0].children[0].value;
           if (loginId.length > 0 && loginId.length < 16) {
               var admin = row.cells[2].getElementsByTagName('input')[0].checked;
               newUsers[loginId] = admin;
           }
       } else if (row.hasAttribute("data-dirty")) {
           var login = row.cells[0];
           var loginId = login.innerHTML;
           var admin = row.cells[2].getElementsByTagName('input')[0].checked;
           updateUsers[loginId] = admin;
       }
    }

    $.ajax({
        url:destUrl,
        data:JSON.stringify({"update":updateUsers, "create":newUsers, "delete":delUsers}),
        dataType:"json",
        contentType: "application/json",
        type:"POST",
        //error:function (jqXHR, textStatus, errorThrown){fplib.msg("errorFunc:"+textStatus);},
        error:function (jqXHR, textStatus, errorThrown){fplib.msg("errorFunc:"+jqXHR.responseText);},
        success:sfunc
    });
};

/*
 * userDelete()
 *
 * NB URL is present as data attribute on row (from the server, see fillUserTable).
 */
fplib.userDelete = function(row) {
    var sfunc = function (data, textStatus, jqXHR) {
        var utab = document.getElementById('userTable');
        fplib.fillUserTable(utab.getAttribute("data-url"))();
    };
    var url = row.getAttribute("data-url");
    if (!url) {
        var utab = row.parentNode.parentNode;
        utab.deleteRow(row.rowIndex);
        return;
    }
    $.ajax({
        url:url,
        dataType:"json",
        contentType: "application/json",
        type:"DELETE",
        error:function (jqXHR, textStatus, errorThrown){alert("errorFunc:"+textStatus);},
        success:sfunc
    });
};

/*
 * addUserTableRow()
 * Add row to user table. Note there are 2 kinds of rows, locally added
 * (user trying to add a new user) and from the server. These rows are
 * different, but thought best to have both done in a single func since
 * a change in one may entail a change in the other.
 */
fplib.addUserTableRow = function(utab, local, url, id, name, admin) {
    var row = utab.insertRow(1); // insert after header row
    if (local) {
        row.setAttribute("data-addedUser", "y"); // flag as local

        // Add login id input field:
        var logid = document.createElement("input");
        logid.type = "text";
        row.insertCell(-1).appendChild(logid);
        row.insertCell(-1).innerHTML = "TBD";  // Name field cannot be set by user.
        row.insertCell(-1).innerHTML = '<input type="checkbox">';  // Admin checkbox initially unchecked
    } else {
        row.setAttribute("data-url", url);
        row.insertCell(-1).innerHTML = id;  // id
        row.insertCell(-1).innerHTML = name;  // name

        // Admin checkbox:
        row.insertCell(-1).innerHTML = '<input type="checkbox" onClick="fplib.setDirty(this, 2)"' +
                (admin ? ' checked' : '') + '>';
    }
    // Delete button:
    var delText = local ? 'Remove' : 'Delete';
    row.insertCell(-1).innerHTML = '<button onClick="fplib.userDelete(this.parentNode.parentNode)">Remove</button>';
};

/*
 * fillUserTable()
 */
fplib.fillUserTable = function () {
    var utab = document.getElementById('userTable');
    var url = utab.getAttribute("data-url");
    var sfunc = function(data) {
        var users = data.users;
        var utab = document.getElementById('userTable');
        utab.innerHTML = "";  // delete any current content
        utab.insertRow(-1).innerHTML = '<th>Id</th><th>Name</th><th>Admin</th>'; // headers
        for (var i=0; i<users.length; ++i) {
            var admin = users[i][3] & 1;
            fplib.addUserTableRow(utab, false, users[i][0], users[i][1], users[i][2], admin);
        }
    };
// error handling?
    $.getJSON(url, sfunc);
}
