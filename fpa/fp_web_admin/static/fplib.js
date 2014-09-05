var fplib = {};

fplib.initTabs = function (tabListId) {
    var tabLinks = {};
    var contentDivs = {};

    function setTab(tabId) {
      // store tabId in session storage for retrieval on navigation back to page:
      if (window.sessionStorage){
        sessionStorage.setItem("currTrialPageTab", tabId);
      }

      // Highlight the selected tab, and dim all others.
      // Also show the selected content div, and hide all others.
      for (var id in contentDivs) {
        if (id == tabId) {
          tabLinks[id].className = 'selected';
          contentDivs[id].className = 'tabContent';
        } else {
          tabLinks[id].className = '';
          contentDivs[id].className = 'tabContent hide';
        }
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

    //-- Code: ------------------------------------------------------
    var i;
    var id;

    // Get the tab links and content divs from the page
    var tabListItems = document.getElementById(tabListId).childNodes;
    for (i = 0; i < tabListItems.length; i++ ) {
      if (tabListItems[i].nodeName == "LI") {
        var tabLink = getFirstChildWithTagName(tabListItems[i], 'A');
        id = getHash(tabLink.getAttribute('href'));
        tabLinks[id] = tabLink;
        contentDivs[id] = document.getElementById(id);
      }
    }

    // Assign onclick events to the tab links, and
    var focusFunc = function() { this.blur(); };
    for (id in tabLinks) {
      tabLinks[id].onclick = showTab;
      tabLinks[id].onfocus = focusFunc;
    }

    var currTab;
    if (window.sessionStorage){
      currTab=sessionStorage.getItem("currTrialPageTab");
      fplib.currTab = currTab
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

