
Number.prototype.pretty = (fix) ->
    if (fix)
        return String(this.toFixed(fix)).replace(/(\d)(?=(\d{3})+\.)/g, '$1,');
    return String(this.toFixed(0)).replace(/(\d)(?=(\d{3})+$)/g, '$1,');


fetch = (url, xstate, callback, snap) ->
    xmlHttp = null;
    # Set up request object
    if window.XMLHttpRequest
        xmlHttp = new XMLHttpRequest();
    else
        xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    xmlHttp.withCredentials = true
    # GET URL            
    xmlHttp.open("GET",  url, true);
    xmlHttp.send(null);

    xmlHttp.onreadystatechange = (state) ->
        if xmlHttp.readyState == 4 and xmlHttp.status == 500
            if snap
                snap(xstate)
        if xmlHttp.readyState == 4 and xmlHttp.status == 200
            if callback
                # Try to parse as JSON and deal with cache objects, fall back to old style parse-and-pass
                try
                    response = JSON.parse(xmlHttp.responseText)
                    callback(response, xstate);
                catch e
                    callback(JSON.parse(xmlHttp.responseText), xstate)

post = (url, args, xstate, callback, snap) ->
    xmlHttp = null;
    # Set up request object
    if window.XMLHttpRequest
        xmlHttp = new XMLHttpRequest();
    else
        xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    xmlHttp.withCredentials = true
    # Construct form data
    ar = []
    for k,v of args
        if v and v != ""
            ar.push(k + "=" + escape(v))
    fdata = ar.join("&")


    # POST URL
    xmlHttp.open("POST", url, true);
    xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xmlHttp.send(fdata);

    xmlHttp.onreadystatechange = (state) ->
        if xmlHttp.readyState == 4 and xmlHttp.status == 500
            if snap
                snap(xstate)
        if xmlHttp.readyState == 4 and xmlHttp.status == 200
            if callback
                # Try to parse as JSON and deal with cache objects, fall back to old style parse-and-pass
                try
                    response = JSON.parse(xmlHttp.responseText)
                    callback(response, xstate);
                catch e
                    callback(JSON.parse(xmlHttp.responseText), xstate)


postJSON = (url, json, xstate, callback, snap) ->
    xmlHttp = null;
    # Set up request object
    if window.XMLHttpRequest
        xmlHttp = new XMLHttpRequest();
    else
        xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    xmlHttp.withCredentials = true
    # Construct form data
    fdata = JSON.stringify(json)

    # POST URL
    xmlHttp.open("POST", url, true);
    xmlHttp.setRequestHeader("Content-type", "application/json");
    xmlHttp.send(fdata);

    xmlHttp.onreadystatechange = (state) ->
        if xmlHttp.readyState == 4 and xmlHttp.status == 500
            if snap
                snap(xstate)
        if xmlHttp.readyState == 4 and xmlHttp.status == 200
            if callback
                # Try to parse as JSON and deal with cache objects, fall back to old style parse-and-pass
                try
                    response = JSON.parse(xmlHttp.responseText)
                    if response && response.loginRequired
                        location.href = "/oauth.html"
                        return
                    callback(response, xstate);
                catch e
                    callback(JSON.parse(xmlHttp.responseText), xstate)



isArray = ( value ) ->
    value and
        typeof value is 'object' and
        value instanceof Array and
        typeof value.length is 'number' and
        typeof value.splice is 'function' and
        not ( value.propertyIsEnumerable 'length' )
        

### isHash: function to detect if an object is a hash ###
isHash = (value) ->
    value and
        typeof value is 'object' and
        not isArray(value)
        

