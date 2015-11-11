/*
 * Create fplib object: A single global variable to hold all the
 * bits and pieces we need access to globally. In a single object
 * so as not to pollute the global namespace too much.
 */
 /* Some magic to prevent warnings in Eclipse: */
 /*global $:false,jQuery:false,alert:false,d3:false*/
var fplib = {};


/*
 * getUrlData
 *
 */
fplib.getUrlData = function (url, sfunc) {
    var cacheDataName = 'tmp_url_' + url;
    var inCache = fplib.hasOwnProperty(cacheDataName);

    if (sfunc === undefined)
        sfunc = function(data) {
            fplib.msg("success:" + JSON.stringify(data));
        };

    // See if data is already got:
    if (fplib.hasOwnProperty(cacheDataName)) {
        sfunc(fplib[cacheDataName]);
    }
    else {
        $.ajax({
            url:url,
            dataType:"json",
            method:"GET",
            error:function (jqXHR, textStatus, errorThrown) {
                fplib.msg("error:"+jqXHR.responseText);
            },
            success:function (data, textStatus, jqXHR) {
                fplib[cacheDataName] = data;
                sfunc(data);
            }
        });
    }
};

/*
 * drawScatterPlot()
 * xdata and ydata are arrays of 2 element arrays - [<nodeId>, <value>],
 * with names xname and yname. These are assumed to both be sorted by <nodeId>.
 * divId, divWidth, divHeight specified the id and dimensions of a div
 * to draw the plot in.
 */
fplib.drawScatterPlot = function(xdata, xname, ydata, yname, divId, divWidth, divHeight) {
    // Clear the svg element from the div, since we want to replace it:
    var theDiv = document.getElementById(divId);
    var svgChild = theDiv.querySelector('svg');
    if (svgChild !== null)
        theDiv.removeChild(svgChild);

    /*
     * Style the div - should this be scoped?:
     */
    var style = document.createElement("style");
    var styleText = document.createTextNode(
        //'#' + divId + ' { font: 10px sans-serif; }' +
        '#splotSvgId' + ' { font: 10px sans-serif; }' +
        '.bar text { fill: #fff; }' +
        '.axis path, .axis line { fill: none; stroke: #000; shape-rendering: crispEdges; }' +
        '.dot { stroke:#000; }' +
        '.tooltip {position:absolute;  width: 200px;  height: 28px;  pointer-events: none;}'
    );
    style.appendChild(styleText);
    theDiv.appendChild(style);

    /*
     * Construct list of points to show. I.e. pairs with both and x and y value for given nodeId.
     * Array point has object element with nodeId, x, and y properties.
     */
    var points = [];
    var xindex = 0;
    var yindex = 0; // what if empty?
    var xlen = xdata.length;
    var ylen = ydata.length;
    while (true) {
        var xnode = xdata[xindex][0];
        var ynode = ydata[yindex][0];
        if (xnode == ynode) {
            points.push({"nodeId":xnode, "x":+xdata[xindex][1], "y":+ydata[yindex][1]});
            // Move on:
            // but what if there's multiple with same node id? take first, hope ordered?
            // Or do cross product?
            // With this code there will be min(x,y) points created for x xdata and y ydata
            // point for a given node.
            ++xindex;
            ++yindex;
        } else if (xnode < ynode) {
            ++xindex;
        } else {
            ++yindex;
        }
        if (yindex === ylen || xindex === xlen)
            break;
    }
    if (points.length <= 0)
        return;  // No points to draw

    /*
     * Make the scatterplot:
     */
    var margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = divWidth - margin.left - margin.right,
        height = divHeight - margin.top - margin.bottom;

    var nodeIdFromPoint = function(d){ return d.nodeId; };

    // x stuff:
    var xValue = function(d){ return d.x; };
    var xScale = d3.scale.linear()
        .domain([d3.min(points, xValue)-1, d3.max(points, xValue)+1])
        .range([0, width]);
    var xMap = function(d) { return xScale(xValue(d));};
    var xAxis = d3.svg.axis().scale(xScale).orient('bottom');

    // y stuff:
    var yValue = function(d){ return d.y; };
    var yScale = d3.scale.linear()
        .domain([d3.min(points, yValue)-1, d3.max(points, yValue)+1])
        .range([height, 0]);
    var yMap = function(d) { return yScale(yValue(d));};
    var yAxis = d3.svg.axis().scale(yScale).orient('left');

    // Add svn canvas to div:
    var svg = d3.select("#" + divId).append("svg")
        .attr("id", "splotSvgId")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // add the tooltip area to the webpage
    var tooltip = d3.select("#" + divId).append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    // x-axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .text(xname);

    // y-axis
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text(yname);

  // draw dots
  svg.selectAll(".dot")
      .data(points)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", xMap)
      .attr("cy", yMap)
      .style("fill", "purple")

      //.style("fill", function(d) { return color(cValue(d));})

      .on("mouseover", function(d) {
          tooltip.transition()
               .duration(200)
               .style("opacity", 0.9);
          tooltip.html("NodeId:" + nodeIdFromPoint(d) + "<br/> (" + xValue(d) + ", " + yValue(d) + ")")
               .style("left", (d3.event.pageX + 5) + "px")
               .style("top", (d3.event.pageY - 28) + "px");
      })
      .on("mouseout", function(d) {
          tooltip.transition()
               .duration(500)
               .style("opacity", 0);
      })

      ;
};

// this not used
fplib.setWrapperWidth = function (elementId) {
    var setWidthTo = Math.round($(".fpHeader").width() - 40);
    document.getElementById(elementId + '_wrapper').style.width = setWidthTo + 'px';
};

fplib.makeTable = function(tdata, tname) {
    var hdrs = tdata.headers;
    var rows = tdata.rows;
    var table  = document.createElement('table');
    table.id = tname;
    var i, j;
    var ncols = hdrs.length;
    var nrows = rows.length;

    // Headers:
    var hrow = table.createTHead().insertRow(0);
    for (i=0; i<ncols; ++i) {
        hrow.insertCell(-1).innerHTML = hdrs[i];
    }

    // Add the rows:
    for (i=0; i<nrows; ++i) {
        var tr = table.insertRow(-1);
        var row = rows[i];
        for (j=0; j<ncols; ++j) {
            tr.insertCell(-1).innerHTML = row[j];
        }
    }

    table.style.width  = '100px';
    table.style.border = "1px solid black";

    document.getElementsByClassName("dataContent")[0].appendChild(table);
};

fplib.makeDataTable = function(tdata, tabid, divName) {
    var hdrs = tdata.headers;
    var rows = tdata.rows;

    // Headers:
    var i, j;
    var ncols = hdrs.length;
    var mycols = [];
    for (i=0; i<ncols; ++i) {
        mycols.push({"title":hdrs[i]});
    }

     var tselect = '#' + tabid;
     jQuery(function() {
         $('#' + divName).html( '<table class="display fptable" width="100%" cellspacing="0" border="0" class="display" id="' + tabid + '"></table>' );

         function setTableWrapperWidth() {
             var setWidthTo = Math.round($(".fpHeader").width() - 40);
             document.getElementById(tabid).style.width = setWidthTo + 'px';
             //$(tselect).dataTable().fnAdjustColumnSizing();
             $(tselect).DataTable().columns.adjust().draw();  // it seems we need the .draw() here
         }

         $(tselect).DataTable( {
             "scrollX": true,
             "fnPreDrawCallback": function() { $(tselect).hide(); },
             "pageLength":10,
             "fnDrawCallback": function() { $(tselect).show(); },
             "fnInitComplete": function(oSettings, json) { $(tselect).show(); },

             "data": rows,
             "columns": mycols
         });
         setTableWrapperWidth(); // This to force on table scroll bar
         window.addEventListener('resize', setTableWrapperWidth);
     });
     // Needed to fix things on reload:
     $(window).load( function () {
         //$(tselect).dataTable().fnAdjustColumnSizing(false);
         $(tselect).DataTable().columns.adjust();//.draw();  // This is the new api way to do this, NB with .draw() it has problems with the header width when vert scrollbar is present.
     } );
};


/*
 * drawHistogram()
 * Draws histogram of given values in the specified (by id) div,
 * which should have the specified width and height.
 * Assumes d3 library is loaded.
 * Parameter values is an array of numbers (passed to the d3 function to make a histogram),
 * valmin and valmax should be the min and max of these.
 */
fplib.drawHistogram = function(values, valmin, valmax, divId, divWidth, divHeight) {
    /*
     * Style the div - should this be scoped?:
     */
    var style = document.createElement("style");
    var styleText = document.createTextNode(
        '#' + divId + ' { font: 10px sans-serif; }' +
        '.bar rect {fill: steelblue; shape-rendering: crispEdges;}' +
        '.bar text { fill: #fff; }' +
        '.axis path, .axis line { fill: none; stroke: #000; shape-rendering: crispEdges; }'
    );
    style.appendChild(styleText);
    document.getElementById(divId).appendChild(style);

    /*
     * Make the hist:
     */
    var margin = {top: 10, right: 30, bottom: 30, left: 30},
        width = divWidth - margin.left - margin.right,
        height = divHeight - margin.top - margin.bottom;

    // temp scale to get the recommended ticks:
    // Note conditional is hack to avoid misfunction when the min equals the max
    // in which case d3.scale.linear would give an empty array of ticks
    // There's probaby a nicer way to present this, but when there's only a single
    // unique value, the histogram is not really of much use anyway..
    var binTicks = valmin < valmax ?
        d3.scale.linear()
            .domain([valmin, valmax])
            .range([0, width])
          .ticks(20)
        : [valmin - 1, valmin + 1];

    var xsc = d3.scale.linear()
        .domain([binTicks[0], binTicks[binTicks.length-1]])
        .range([0, width]);

    // Generate a histogram using twenty uniformly-spaced bins.
    var data = d3.layout.histogram()
        .bins(binTicks)
        (values);

    var ysc = d3.scale.linear()
        .domain([0, d3.max(data, function(d) { return d.y; })])
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xsc)
        .orient("bottom");

    var svg = d3.select("#" + divId).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var bar = svg.selectAll(".bar")
        .data(data)
      .enter().append("g")
        .attr("class", "bar")
        .attr("transform", function(d) { return "translate(" + xsc(d.x) + "," + ysc(d.y) + ")"; });

    bar.append("rect")
        .attr("x", 1)
        .attr("width", xsc(data[0].x + data[0].dx) - 1)
        .attr("height", function(d) { return height - ysc(d.y); });

    var formatCount = d3.format(",.0f"); // counts format function
    bar.append("text")
        .attr("dy", ".75em")
        .attr("y", 6)
        .attr("x", xsc(data[0].x + data[0].dx) / 2)
        .attr("text-anchor", "middle")
        .text(function(d) { return formatCount(d.y); });
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);
};


/*
 * initTabs()
 * parameter tabListId should be the id of a UL element containing links
 * for the desired tabs. Each LI should be an anchor for the relevant div
 * on the page.
 * Note all the styling is done in this function. There is no separate css
 * required.
 */
fplib.STORAGE_TAG = "fpCurrTrialPageTab";
fplib.initTrialTabs = function() {
    $('a[data-toggle="tab"]').on('click', function(e) {
        var tabref = $(this).attr('href');
        if (window.sessionStorage)
            sessionStorage.setItem(fplib.STORAGE_TAG, tabref);
    });

    var currTab;
    if (window.sessionStorage) {
        currTab = sessionStorage.getItem(fplib.STORAGE_TAG);
        var activeTab = $('[href=' + currTab + ']');
        if (activeTab.length) {
            activeTab.tab('show');
        } else {
            $('.nav-tabs a:first').tab('show');
        }
    }
};

/*
 * gotoLocationAndClearLastTab()
 * Goes to the specified location, but also clears memory of current
 * trial tab.
 */
fplib.gotoLocationAndClearLastTab = function(newLocation) {
    sessionStorage.removeItem(fplib.STORAGE_TAG);
    if (newLocation !== 0)
        window.location=newLocation;
};


fplib.OLDinitTabs = function (tabListId) { // this version no longer used, using bootstrap tabs instead
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
          contentDivs[id].style.display = "";
        } else {
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
    var firstId;  // The first tab is made visible by default.
                  // NB if no tab is made visible datatables doesn't display properly

    // Get the tab list element and style it:
    var tabListElement = document.getElementById(tabListId);
    tabListElement.style.listStyleType = 'none';
    tabListElement.style.whiteSpace = 'nowrap';
    tabListElement.style.margin = '30px 0 0 0';
    tabListElement.style.padding = '0';

    // Process the children:
    var tabListItems = tabListElement.children;
    for (i = 0; i < tabListItems.length; i++ ) {
      if (tabListItems[i].nodeName == "LI") {
        // style the li:
        tabListItems[i].style.display = 'inline-block';
        tabListItems[i].style.margin = '0';

        var tabLink = getFirstChildWithTagName(tabListItems[i], 'A');
        id = getHash(tabLink.getAttribute('href'));

        if (i === 0) {
            // MFK HACK, attow first tab is only one with datatables,
            // and this needs to be made visible to display properly.
            firstId = id;
        }
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
      currTab = sessionStorage.getItem(STORAGE_TAG);
      if (!currTab) {
          currTab = firstId;
      }
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
};

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
        var errs = data.errors;
        if (errs && errs.length > 0)
            fplib.msg("errors found:" + JSON.stringify(errs));
        fplib.fillUserTable();
    };

    for (var i = 1, row; row = table.rows[i]; i++) {
       var loginId;
       if (row.hasAttribute("data-addedUser")) {
           loginId = row.cells[0].children[0].value;
           if (loginId.length > 0 && loginId.length < 16) {
               newUsers[loginId] = row.cells[2].getElementsByTagName('input')[0].checked; // admin field
           }
       } else if (row.hasAttribute("data-dirty")) {
           var login = row.cells[0];
           loginId = login.innerHTML;
           updateUsers[loginId] = row.cells[2].getElementsByTagName('input')[0].checked; // admin field
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
        fplib.fillUserTable();
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

