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
    var STORAGE_TAG = "fpCurrTrialPageTab"

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
        tabLink.style.color = selected ? '#000' : '#42454a';
        tabLink.style.backgroundColor = selected ? '#f1f0ee' : 'pink';
        tabLink.style.padding = selected ? '0.7em 0.3em 0.38em 0.3em' : '0.3em';

        tabLink.style.minWidth = '120px';
        tabLink.style.display = 'block';
        tabLink.style.border = '1px solid #c9c3ba';
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
    tabListElement.style.padding = '0 0 0.3em 0';

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

