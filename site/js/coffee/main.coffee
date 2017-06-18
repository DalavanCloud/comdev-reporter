jsdata = {}
rendered = {}

templates = {}
nproject = null;
animals = ['hedgehogs', 'cows', 'geese', 'pigs', 'fluffy kittens', 'puppies', 'rabid dogs', 'ponies', 'weevils']

# This is faster than parseInt, and it's more obvious what is being done
toInt = (number) ->
    return number | 0



makeSelect = (name, arr) ->
    sel = new HTML('select', { name: name})
    for val in arr
        opt = new HTML('option', { value: val})
        opt.inject(val)
        sel.inject(opt)
    return sel


getWednesdays = (mo, y) ->
    d = new Date();
    if mo
        d.setMonth(mo);
    if y
        d.setFullYear(y, d.getMonth(), d.getDate())
    
    month = d.getMonth()
    wednesdays = []

    d.setDate(1)

    # Get the first Wednesday (day 3 of week) in the month
    while d.getDay() != 3
        d.setDate(d.getDate() + 1)
    

    # Get all the other Wednesdays in the month
    while d.getMonth() == month
        wednesdays.push(new Date(d.getTime()))
        d.setDate(d.getDate() + 7)
        
    return wednesdays;

# check if the entry is a wildcard month

everyMonth = (s) ->
    if (s.find('Next month') != -1)
        return true
    return s == 'Every month'


m = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Format the report month array. Assumes that non-month values appear first

formatRm = (array) ->
    first = array[0]
    if array.length == 1
        return first
    if first not in m
        return  first.concat('; (default: ', array.slice(1).join(', '),')')
    return array.join(', ')

# Called by: GetAsyncJSON("reportingcycles.json?" + Math.random(), [pmc, reportdate, json.pdata[pmc].name], setReportDate) 

setReportDate = (json, x) ->
    pmc = x[0]
    reportdate = x[1]
    fullname = (x[2] or "Unknown").replace(/Apache /, "")
    today = new Date()

    # the entries must be in date order
    dates = [] 
    if not pmc in json
        pmc = fullname
    
    #reporting months for the pmc
    rm = json[pmc]

    # First check if the list contains an every month indicator
    # This is necessary to ensure that the dates are added to the list in order
    for sm in json[pmc]
        if everyMonth(sm)
            # Reset to every month
            rm = m
            break

    # Check the months in order, so it does not matter if the data is unordered
    for x in m
        for i in rm
            if (m[x] == rm[i])
                dates.push(getWednesdays(x)[2])

    # Cannot combine with the code above because that would destroy the order
    ny = today.getFullYear() + 1
    for x in m
        for i in rm
            if (m[x] == rm[i])
                dates.push(getWednesdays(x, ny)[2])

    nextdate = dates[0];
    while (nextdate < today)
        nextdate = dates.shift()
    
    
    reportdate.innerHTML += "<b>Reporting schedule:</b> " + (if json[pmc] then formatRm(json[pmc]) else "Unknown(?)") + "<br>"
    reportdate.innerHTML += "<b>Next report date: " + (if nextdate then nextdate.toDateString() else "Unknown(?)") + "</b>"
    if (nextdate)
        link = "https://svn.apache.org/repos/private/foundation/board/board_agenda_" + nextdate.getFullYear() +
            "_" + (if nextdate.getMonth() < 9 then "0" else "") + (nextdate.getMonth() + 1) + "_" + nextdate.getDate() + ".txt"
        reportdate.innerHTML += "<br>File your report in <a href='" + link + "'>" + link + "</a> when it has been seeded."
    

buildPanel = (pmc, title) ->
    parent = document.getElementById('tab_' + pmc);

    toc = document.getElementById('toc_' + pmc);
    if (!toc)
        toc = document.createElement('cl')
        toc.setAttribute("class", "sub-nav")
        toc.setAttribute("id", "toc_" + pmc)
        if (parent.firstChild.nextSibling)
            parent.insertBefore(toc, parent.firstChild.nextSibling);
        else
            parent.appendChild(toc)
        
    linkname = title.toLowerCase().replace(/[^a-z0-9]+/, "")
    li = document.createElement('dd');
    li.setAttribute("role", "menu-item")
    li.innerHTML = "<a href='#" + linkname + "_" + pmc + "'>" + title + "</a>"
    toc.appendChild(li)

    div = document.createElement('div')
    div.setAttribute("id", linkname + "_" + pmc);
    parent.appendChild(div)

    titlebox = document.createElement('div');
    titlebox.innerHTML = "<h3 style='background: #666; color: #EEE; border: 1px solid #66A; margin-top: 30px;'>" + title + " &nbsp; &nbsp; <small> <b>&uarr;</b> <a href='#tab_" + pmc + "'>Back to top</a></small></h3>"
    div.appendChild(titlebox);
    return div


addLine = (pmc, line) ->
    line = if line then line else "  "
    lines = line.split(/\n/)
    for xline in lines
        words = xline.split(" ")
        len = 0
        out = ""
        for word, i in words
            len += word.replace(/<.+?>/, "").length + (if i == words.length - 1 then 0 else 1)
            if (len >= 78)
                out += "\n   "
                len = words[i].replace(/<.+?>/, "").length + (if i == words.length - 1 then 0 else 1)
            out += words[i] + " "
        templates[pmc] += out + "\n"


isNewPMC = (json,pmc,after) ->
    return json.pmcdates[pmc].pmc[1] >= (after.getTime() / 1000)


PMCchanges = (json, pmc, after) ->
        changes = buildPanel(pmc, "PMC changes (from committee-info)");
        
        roster = json.pmcdates[pmc].roster
        nc = 0; # newest committer start date
        np = 0; # newest pmc member start date
        ncn = null; # newest committer name
        npn = null; # newest pmc name
        afterTime = after.getTime() / 1000
        pmcStartTime = json.pmcdates[pmc].pmc[2]

        addLine(pmc, "## PMC changes:")
        addLine(pmc)
        if (pmcStartTime > afterTime) 
            afterTime = pmcStartTime
            changes.innerHTML += "<h5>Changes since PMC creation:</h5>"
        else
            changes.innerHTML += "<h5>Changes within the last 3 months:</h5>"
        

        # pre-flight check
        c = 0; # total number of pmc members
        npmc = 0; # number of recent pmc members
        for k, entry of roster
            c++
            if (entry[1] > afterTime)
                npmc++;
        addLine(pmc, " - Currently " + c + " PMC members.")
        if (npmc > 1)
            addLine(pmc, " - New PMC members:")
        

        for k, entry of roster
            if (entry[1] > np) # find most recent member
                np = entry[1]    # start date
                npn = entry[0];  # full name
            
            if (entry[1] > afterTime)
                changes.innerHTML += "&rarr; " + entry[0] + " was added to the PMC on " + new Date(entry[1] * 1000).toDateString() + "<br>";
                addLine(pmc, (if npmc > 1 then "   " else "") + " - " + entry[0] + " was added to the PMC on " + new Date(entry[1] * 1000).toDateString())

        if (npmc == 0)
            addLine(pmc, " - No new PMC members added in the last 3 months")
            changes.innerHTML += "&rarr; <font color='red'><b>No new PMC members in the last 3 months.</b></font><br>";
        
        if (npn)
            if (np < afterTime)
                addLine(pmc, " - Last PMC addition was " + npn + " on " + new Date(np * 1000).toDateString())
            changes.innerHTML += "&rarr; " + "<b>Last PMC addition: </b>" + new Date(np * 1000).toDateString() + " (" + npn + ")<br>"
        
        changes.innerHTML += "&rarr; " + "<b>Currently " + c + " PMC members.<br>"
        changes.innerHTML += "<br>PMC established: " + json.pmcdates[pmc].pmc[0]
        if (pmcStartTime > 0) # don't use missing time
            changes.innerHTML += " (assumed actual date: " + epochSecsYYYYMMDD(pmcStartTime) + ")"
        addLine(pmc)


epochSecsYYYYMMDD = (t) =>
    new Date(t * 1000).toISOString().slice(0, 10)


renderFrontPage = (tpmc) ->
    thisHour = toInt(new Date().getTime() / (3600*1000)) # this changes once per hour
    container = document.getElementById('contents')
    top = document.createElement('div');
    container.appendChild(top)
    json = jsdata
    sproject = tpmc;
    hcolors = ["#000070", "#007000", "#407000", "#70500", "#700000", "#A00000"]
    hvalues = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
    container.innerHTML = ""
    for pmc, i in json.pmcs
        if pmc == tpmc or not tpmc
            # If we already rendered this, just re-add it
            if rendered[pmc]
                container.appendChild(rendered[pmc])
            # Stuff has broken, check that we have dates!
            if (not pmc in json.pmcdates)
                continue
            
            templates[pmc] = ""
    
            addLine(pmc, "## Description:")
            if ('shortdesc' in jsdata.pdata[pmc])
                addLine(pmc, "   " + json.pdata[pmc].shortdesc)
            else
                addLine(pmc, " - <font color='red'>Description goes here</font>")
            
            addLine(pmc)
    
            a = animals[Math.floor(Math.random()*animals.length*0.999)]
            addLine(pmc, "## Issues:")
            addLine(pmc, " - <font color='red'>TODO - list any issues that require board attention, \n  or say \"there are no issues requiring board attention at this time\" - if not, the " + a + " will get you.</font>")
            addLine(pmc)
    
            addLine(pmc, "## Activity:")
            addLine(pmc, " - <font color='red'>TODO - the PMC <b><u>MUST</u></b> provide this information</font>")
            addLine(pmc)
    
            
            a = animals[Math.floor(Math.random()*animals.length*0.999)]
            addLine(pmc, "## Health report:")
            addLine(pmc, " - <font color='red'>TODO - Please use this paragraph to elaborate on why the current project activity (mails, commits, bugs etc) is at its current level - Maybe " + a + " took over and are now controlling the project?</font>")
            addLine(pmc)
    
            obj = document.createElement('div');
            rendered[pmc] = obj
            obj.setAttribute("id", "tab_" + pmc)
            obj.style = "padding: 10px; text-align: left !important;"
            obj.setAttribute("aria-hidden", "true")
            title = document.createElement('h2')
            title.innerHTML = json.pdata[pmc].name or pmc
            obj.appendChild(title)
            health = document.createElement('p');
            if (json.health[pmc] && !isNaN(json.health[pmc]['cscore']))
                health.style.marginTop = "10px"
                health.innerHTML = "<b>Committee Health score:</b> <a href='chi.py#" + pmc + "'><u><font color='" + hcolors[json.health[pmc]['cscore']] + "'>" + (6.33 + (json.health[pmc]['score'] * -1.00 * (20 / 12.25))).toFixed(2) + " (" + hvalues[json.health[pmc]['cscore']] + ")</u></font></a> <i>(This is an automatically generated score, it is NOT authoritative in any way!)</i>"
                obj.appendChild(health)
            
            container.appendChild(obj)
    
    
    
            # Report date
    
            reportdate = buildPanel(pmc, "Report date")
            if (json.pdata[pmc].chair)
                reportdate.innerHTML += "<b>Committee Chair: </b>" + json.pdata[pmc].chair + "<br>"
            
    
            fetch("reportingcycles.json?" + thisHour, [pmc, reportdate, json.pdata[pmc].name], setReportDate)
    
    
            # LDAP committee + Committer changes
    
            mo = new Date().getMonth() - 3;
            after = new Date();
            after.setMonth(mo); # This also works if mo is negative
            PMCchanges(json, pmc, after);
    
            changes = buildPanel(pmc, "PMC changes (From LDAP)");
    
            c = 0; # total number of committer + pmc changes since establishment
            cu = 0; # total number of committer (user) changes
            for x,y of json.changes[pmc].committer
                cu++;
                c++;
            for x,y of json.changes[pmc].pmc
                c++;
            nc = 0; # newest committer date
            np = 0; # newest pmc date
            ncn = null; # newest committer name
            npn = null; # newest pmc name
    
            addLine(pmc, "## Committer base changes:")
            addLine(pmc)
            addLine(pmc, " - Currently " + json.count[pmc][1] + " committers.")
            if (cu == 0) # no new committers
                if (isNewPMC(json,pmc,after))
                    addLine(pmc, " - No changes (the PMC was established in the last 3 months)")
                else
                    addLine(pmc, " - No new changes to the committer base since last report.")
                addLine(pmc)
            
            if (c == 0) # no changes at all
                if (isNewPMC(json,pmc,after))
                    changes.innerHTML += "No changes - the PMC was established in the last 3 months."
                else
                    changes.innerHTML += "<font color='red'><b>No new changes to the PMC or committer base detected - (LDAP error or no changes for &gt;2 years)</b></font>"
                
            else
                changes.innerHTML += "<h5>Changes within the last 3 months:</h5>"
    
                # pre-flight check
                npmc = 0; # recent committee group additions
                for k, entry of json.changes[pmc].pmc
                    if (entry[1] > after.getTime() / 1000)
                        npmc++;
                    
                for k, entry of json.changes[pmc].pmc
                    if (entry[1] > np) # latest pmc member date
                        np = entry[1]
                        npn = entry[0]; # latest pmc member name
                    
                    if (entry[1] > after.getTime() / 1000)
                        changes.innerHTML += "&rarr; " + entry[0] + " was added to the PMC on " + new Date(entry[1] * 1000).toDateString() + "<br>"
    
                if (npmc == 0) # PMC older than 3 months itself
                    if (isNewPMC(json,pmc,after))
                        changes.innerHTML += "&rarr; No new PMC members in the 3 months since the PMC was established<br>";
                    else
                        changes.innerHTML += "&rarr; <font color='red'><b>No new PMC members in the last 3 months.</b></font><br>";
                    
                if (npn)
                    changes.innerHTML += "&rarr; " + "<b>Last PMC addition: </b>" + new Date(np * 1000).toDateString() + " (" + npn + ")<br>"
                
    
    
                # pre-flight check
                ncom = 0; # number of new committers
                for k, entry of json.changes[pmc].committer
                    if (entry[1] > after.getTime() / 1000) # entry[1] is the first seen timestamp
                        ncom++;
    
                if (ncom > 1)
                    addLine(pmc, " - New commmitters:")
                
                for k, entry of json.changes[pmc].committer
                    if (entry[1] > nc) # find the most recent entry
                        nc = entry[1]  # the timestamp
                        ncn = entry[0];# full name
                    
                    if (entry[1] > after.getTime() / 1000)
                        changes.innerHTML += "&rarr; " + entry[0] + " was added as a committer on " + new Date(entry[1] * 1000).toDateString() + "<br>"
                        addLine(pmc, (if ncom > 1 then "   " else "") + " - " + entry[0] + " was added as a committer on " + new Date(entry[1] * 1000).toDateString())
                    
                if (ncom == 0) 
                    changes.innerHTML += "&rarr; <font color='red'><b>No new committers in the last 3 months.</b></font><br>";
                    addLine(pmc, " - No new committers added in the last 3 months")
                
    
                if (ncn) 
                    if (nc < after.getTime() / 1000)
                        addLine(pmc, " - Last committer addition was " + ncn + " at " + new Date(nc * 1000).toDateString())
                    changes.innerHTML += "&rarr; " + "<b>Last committer addition: </b>" + new Date(nc * 1000).toDateString() + " (" + ncn + ")<br>"
                else
                    addLine(pmc, " - Last committer addition was more than 2 years ago")
                    changes.innerHTML += "&rarr; " + "<b>Last committer addition: </b><font color='red'>more than two years ago (not in the archive!)</font><br>"
                
                changes.innerHTML += "&rarr; " + "<b>Currently " + json.count[pmc][1] + " committers and " + json.count[pmc][0] + " PMC members."
                addLine(pmc)
            
            
            # Release data
    
            releases = buildPanel(pmc, "Releases")
            addLine(pmc, "## Releases:")
            addLine(pmc)
            nr = 0;
            lr = null;
            lrn = 0;
            tr = 0
            for version, date of json.releases[pmc]
                tr++;
                if (date > lrn)
                    lrn = date
                    lr = version
                
                if (date >= after.getTime() / 1000)
                    err = ""
                    if (new Date(date * 1000) > new Date())
                        err = " (<font color='red'>This seems wrong?!</font>)"
                    
                    releases.innerHTML += "&rarr; " + "<b>" + version + "</b> was released on " + new Date(date * 1000).toDateString() + err + "<br>"
                    addLine(pmc, " - " + version + " was released on " + new Date(date * 1000).toDateString() + err)
                    nr++;
    
            if (nr == 0)
                if (lr)
                    releases.innerHTML += "&rarr; " + "<b>Last release was " + lr + ", released on </b>" + new Date(lrn * 1000).toDateString() + "<br>"
                    addLine(pmc, " - Last release was " + lr + " on " + new Date(lrn * 1000).toDateString())
                    if (lr.match("incubat") && !isNewPMC(json,pmc,after))
                        releases.innerHTML += "<br><font color='red'><b>No release since graduation</b></font><br><br>"
                        addLine(pmc, " - <font color='red'><b>No release since graduation??? [FIX!]</b></font>")
                else
                    releases.innerHTML += "No release data could be found.<br>"
                    addLine(pmc, " - <font color='red'>No release data could be found [FIX!]</font>")
    
            releases.innerHTML += "<i>(A total of " + (tr - nr) + " older release(s) were found for " + pmc + " in our db)</i><br>"
            releases.innerHTML += "<br><a href='javascript:void(0);' onclick=\"$('#rdialog_" + pmc + "').dialog({minWidth: 450, minHeight: 240});\">Add a release</a>"
            releases.innerHTML += " - <a href='javascript:void(0);' onclick=\"$('#dialog_" + pmc + "').dialog({minWidth: 450, minHeight: 240});\">Fetch releases from JIRA</a>"
            releases.innerHTML += " - <a href='addrelease.html?" + pmc + "'>Manage release versions</a><br>"
    
            if (tr > 0)
                div = renderReleaseChart(json.releases[pmc], pmc, releases);
                releases.appendChild(div)
            
            addLine(pmc)
    
            mlbox = buildPanel(pmc, "Mailing lists");
    
            ul = document.createElement('ul')
            ul.style.textAlign = "left;"
            mlbox.appendChild(ul)
            prev = ""
            f = 0
            addLine(pmc, "## Mailing list activity:")
            addLine(pmc)
            addLine(pmc, " - <font color='red'>TODO Please explain what the following statistics mean for the project." +
                    " If there is nothing significant in the figures, omit this section.</font>")
            addLine(pmc)
            
            first = ['users', 'dev', 'commits', 'private', 'bugs', 'modules-dev'];
            
            
            for i,x of first
                ml = pmc + ".apache.org-" + first[i]
                if (ml != prev && ml.search("infra") < 0 && json.mail[pmc] && json.mail[pmc][ml]) 
                    f++;
                    prev = ml
                    d = ml.split(".org-");
                    mlname = d[1] + "@" + d[0] + ".org"
                    lookup = d[0].split(/\./)[0] + "-" + d[1]
    
                    x = renderChart(json.mail[pmc], ml, obj, if (json.delivery[pmc] && json.delivery[pmc][lookup]) then json.delivery[pmc][lookup].weekly else {})
                    total = x[0]
                    diff = x[1]
                    div = x[2]
    
                    add = ""
                    if (json.delivery[pmc] && json.delivery[pmc][lookup])
                        add = ":\n    - " + json.delivery[pmc][lookup].quarterly[0] + " emails sent to list (" + json.delivery[pmc][lookup].quarterly[1] + " in previous quarter)";
                    
                    text = "Currently: " + total + " subscribers <font color='green'>(up " + diff + " in the last 3 months)</font>"
                    if (diff < 0) 
                        text = "Currently: " + total + " subscribers <font color='red'>(down " + diff + " in the last 3 months)</font>"
                        if (d[1] != "private" && d[1] != "security" && d[1] != "commits")
                            addLine(pmc, " - " + mlname + ": ")
                            addLine(pmc, "    - " + total + " subscribers (down " + diff + " in the last 3 months)" + add)
                            addLine(pmc)
                    else
                        if (d[1] != "private" && d[1] != "security" && d[1] != "commits")
                            addLine(pmc, " - " + mlname + ": ")
                            addLine(pmc, "    - " + total + " subscribers (up " + diff + " in the last 3 months)" + add)
                            addLine(pmc)
    
                    if (json.delivery[pmc] && json.delivery[pmc][lookup])
                        text += " (" + json.delivery[pmc][lookup].quarterly[0] + " emails sent in the past 3 months, " + json.delivery[pmc][lookup].quarterly[1] + " in the previous cycle)"
    
                    p = document.createElement('li');
                    p.innerHTML = "<h5>" + mlname + ":</h5>" + text
                    p.appendChild(div)
                    ul.appendChild(p)
                    
            for ml of json.mail[pmc]
                skip = false
                for i in first
                    xml = pmc + ".apache.org-" + first[i]
                    if (ml.search(xml) == 0)
                        skip = true
                if (!skip)
    
                    f++;
                    if (ml != prev && ml.search("infra") < 0)
                        prev = ml
                        d = ml.split(".org-");
                        mlname = d[1] + "@" + d[0] + ".org"
                        lookup = d[0].split(/\./)[0] + "-" + d[1]
                        x = renderChart(json.mail[pmc], ml, obj, if (json.delivery[pmc] && json.delivery[pmc][lookup]) then json.delivery[pmc][lookup].weekly else {})
                        total = x[0]
                        diff = x[1]
                        div = x[2]
    
                        add = ""
                        if (json.delivery[pmc] && json.delivery[pmc][lookup])
                            add = ":\n    - " + json.delivery[pmc][lookup].quarterly[0] + " emails sent to list (" + json.delivery[pmc][lookup].quarterly[1] + " in previous quarter)";
                        
                        text = "Currently: " + total + " subscribers <font color='green'>(up " + diff + " in the last 3 months)</font>"
                        if (diff < 0) 
                            text = "Currently: " + total + " subscribers <font color='red'>(down " + diff + " in the last 3 months)</font>"
                            if (d[1] != "private" && d[1] != "security" && d[1] != "commits") 
                                addLine(pmc, " - " + mlname + ": ")
                                addLine(pmc, "    - " + total + " subscribers (down " + diff + " in the last 3 months)" + add)
                                addLine(pmc)
                        else
                            if (d[1] != "private" && d[1] != "security" && d[1] != "commits")
                                addLine(pmc, " - " + mlname + ": ")
                                addLine(pmc, "    - " + total + " subscribers (up " + diff + " in the last 3 months)" + add)
                                addLine(pmc)
    
                        if (json.delivery[pmc] && json.delivery[pmc][lookup])
                            text += " (" + json.delivery[pmc][lookup].quarterly[0] + " emails sent in the past 3 months, " + json.delivery[pmc][lookup].quarterly[1] + " in the previous cycle)"
    
                        p = document.createElement('li');
                        p.innerHTML = "<h5>" + mlname + ":</h5>" + text
                        p.appendChild(div)
                        ul.appendChild(p)
                        
            addLine(pmc)
            
            if json.bugzilla[pmc][0] or json.bugzilla[pmc][1] > 0
                renderBZ(pmc)
            
    
            if json.jira[pmc][0] > 0 or json.jira[pmc][1] > 0 
                renderJIRA(pmc)
            
    
    
            # Reporting example
            template = buildPanel(pmc, "Report template");
            template.innerHTML += "<pre style='border: 2px dotted #444; padding: 10px; background: #FFD;' contenteditable='true'>" + templates[pmc] + "</pre>"
    
            # Fetch from JIRA dialog
            dialog = document.createElement('div');
            dialog.setAttribute("id", "dialog_" + pmc);
            dialog.setAttribute("title", "Fetch data from JIRA for " + pmc)
            dialog.setAttribute("style", "display: none;")
            if (jsdata.keys[pmc] && jsdata.keys[pmc].length > 0)
                dialog.innerHTML = "<p>Suggested JIRA Keys: <kbd>" + jsdata.keys[pmc].join(", ") + "</kbd></p>"
            else
                dialog.innerHTML = "<p>No JIRA keys found - are you sure this project uses JIRA?</p>"
            
            dialog.innerHTML += "<form><b>JIRA Project:</b><input type='text' name='jira' placeholder='FOO'><br><b>Optional prepend:</b> <input name='prepend' type='text' placeholder='Foo'/><br>"+
                               "<input type='button' value='Fetch from JIRA' onclick='fetchJIRA(\"" + pmc + "\", this.form[\"jira\"].value, this.form[\"prepend\"].value);'></form>"+
                               "<p>If you have multiple JIRA projects and they only have the version number in their release versions, please enter the component name in the 'prepend' field.</p>"
            document.getElementById('tab_' + pmc).appendChild(dialog)
    
            # Manually add release dialog
            rdialog = document.createElement('div');
            rdialog.setAttribute("id", "rdialog_" + pmc);
            rdialog.setAttribute("title", "Add a release for " + pmc)
            rdialog.setAttribute("style", "display: none;")
            rdialog.innerHTML = "<form><b>Version:</b><input type='text' name='version' placeholder='1.2.3'><br>"+
                                "<b>Date:</b> <input name='date' type='text' placeholder='YYYY-MM-DD'/><br>"+
                                "<input type='button' value='Add release' onclick='addRelease(\"" + pmc + "\", this.form[\"version\"].value, this.form[\"date\"].value);'></form>"
            container.appendChild(rdialog)

        
            



renderJIRA  = (pmc) ->
    obj = buildPanel(pmc, "JIRA Statistics")

    addLine(pmc, "## JIRA activity:")
    addLine(pmc)
    addLine(pmc, " - " + jsdata.jira[pmc][0] + " JIRA tickets created in the last 3 months");
    addLine(pmc, " - " + jsdata.jira[pmc][1] + " JIRA tickets closed/resolved in the last 3 months");
    addLine(pmc)
    obj.innerHTML += jsdata.jira[pmc][0] + " JIRA tickets created in the last 3 months<br>";
    obj.innerHTML += jsdata.jira[pmc][1] + " JIRA tickets closed/resolved in the last 3 months<br>";
    if (jsdata.keys[pmc])
        obj.innerHTML += "Keys used: <kbd>" + jsdata.keys[pmc].join(", ") + "</kbd><br>"
    
    obj.innerHTML += "Keys with tickets: <kbd>" + jsdata.jira[pmc][2].join(", ") + "</kbd>"


renderBZ = (pmc) ->
    obj = buildPanel(pmc, "Bugzilla Statistics")

    addLine(pmc, "## Bugzilla Statistics:")
    addLine(pmc)
    addLine(pmc, " - " + jsdata.bugzilla[pmc][0] + " Bugzilla tickets created in the last 3 months");
    addLine(pmc, " - " + jsdata.bugzilla[pmc][1] + " Bugzilla tickets resolved in the last 3 months");
    addLine(pmc)
    obj.innerHTML += jsdata.bugzilla[pmc][0] + " Bugzilla tickets created in the last 3 months<br>";
    obj.innerHTML += jsdata.bugzilla[pmc][1] + " Bugzilla tickets resolved in the last 3 months<br>";
    obj.innerHTML += "Tickets were found for the following products:<br><kbd>" + Object.keys(jsdata.bugzilla[pmc][2]).sort().join(", ") + "</kbd>"


renderChart = (json, name, container, delivery) ->

    chartDiv = document.createElement('div')
    chartDiv.setAttribute("id", name + "_chart")
    dates = []
    noweekly = 0;
    for date, count of json[name]
        dates.push(date)
    for date, count of delivery
        noweekly++;
    d = name.split(".org-");
    mlname = d[1] + "@" + d[0] + ".org"
    dates.sort();
    cu = 0;
    narr = []
    hitFirst = false

    dp = new Date();
    dp.setMonth(dp.getMonth() - 3);

    odp = new Date();
    odp.setMonth(odp.getMonth() - 6);

    difference = 0
    for date in dates
        dateString = new Date(parseInt(date) * 1000);
        if (dateString > dp) 
            difference += json[name][date]
        
        cu = cu + json[name][date];
        if (cu > 0) 
            hitFirst = true
        
        if ((cu > 0 || hitFirst) && dateString >= odp) 
            if (noweekly > 0) 
                narr.push([dateString, cu, delivery[date] or 0])
            else
                narr.push([dateString, cu])
            
    data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', "List members");
    if (noweekly > 0)
        data.addColumn('number', "Emails sent per week");
    
    data.addRows(narr);


    options = {
        title: 'Mailing list stats for ' + mlname,
        backgroundColor: 'transparent',
        width: 900,
        height: 260,
        legend: {
            position: 'none',
            maxLines: 3
        },
        vAxis: {
            format: "#"
        },
        vAxes: if (noweekly > 0) then [

            {
                title: 'Emails per week',
                titleTextStyle: {
                    color: '#DD0000'
                },
                min: 0
            }, {
                title: 'Subscribers',
                titleTextStyle: {
                    color: '#0000DD'
                },
                min: 0,
                minValue: 0
            },
        ] else [{
                title: 'Subscribers',
                titleTextStyle: {
                    color: '#0000DD'
                }
            },
        ],
        series: {
            0: {
                type: "line",
                pointSize: 4,
                lineWidth: 2,
                targetAxisIndex: if (noweekly > 0) then 1 else null
            },
            1: {
                type: "bars",
                targetAxisIndex: if (noweekly > 0) then 0 else [0, 1]
            }
        },
        seriesType: "bars",
        tooltip: {
            isHtml: true
        },
    };

    chart = new google.visualization.ComboChart(chartDiv);

    chart.draw(data, options);
    return [cu, difference, chartDiv];



renderReleaseChart = (releases, name, container) ->
    chartDiv = null
    if (document.getElementById(name + "_releasechart"))
        chartDiv = document.getElementById(name + "_releasechart")
    else
        chartDiv = document.createElement('div')
        chartDiv.setAttribute("id", name + "_releasechart")

    narr = []
    maxLen = 1;
    for version, date of releases
        x = version.match(/(\d+)\.(\d+)/)
        if (x && x[2].length > maxLen)
            maxLen = x[2].length;
    
    for version, date of releases
        if (new Date(releases[version] * 1000).getFullYear() >= 1999)
            major = parseFloat(version) or 1
            x = version.match(/(\d+)\.(\d+)/)
            if (x)
                while (x[2].length < maxLen)
                    x[2] = "0" + x[2]
                major = parseFloat(x[1] + "." + x[2])

            narr.push([new Date(releases[version] * 1000), major, version + " - " + new Date(releases[version] * 1000).toDateString()])

    data = new google.visualization.DataTable();

    data.addColumn('datetime', 'Date');
    data.addColumn('number', 'Version')
    data.addColumn('string', 'tooltip');
    data.setColumnProperty(2, 'role', 'tooltip');

    data.addRows(narr);


    options = {
        title: 'Release timeline for ' + name,
        height: 240,
        width: 800,
        backgroundColor: 'transparent',
        series: [{
                pointSize: 15
            },
        ],
        pointShape: {
            type: 'star',
            sides: 5
        }
    };

    chart = new google.visualization.ScatterChart(chartDiv);
    chartDiv.style.marginLeft = "50px";

    chart.draw(data, options);
    return chartDiv


fetchJIRA = (pmc, project, prepend) ->
    if (project && project.length > 1)
        fetch("jiraversions.py?project=" + pmc + "&jiraname=" + project + "&prepend=" + prepend, null,
            (json) ->
                if json && json.versions
                    for version in json.versions
                        jsdata.releases[pmc][version] = json.versions[version]
                    
                    $('#dialog_' + pmc).dialog("close")
                    nproject = pmc
                    alert("Fetched " + json.added + " releases from JIRA!")
                    renderFrontPage(jsdata)
                else if (json && json.status)
                    alert(json.status)
                else if (json)
                    alert(JSON.stringify(json))
                else
                    alert("Couldn't find any release data :(")
        )


addRelease = (pmc, version, date) ->
    if (version && version.length > 1 && date.match(/^(\d\d\d\d)-(\d\d)-(\d\d)$/))
        x = date.split("-");
        y = new Date(x[0], parseInt(x[1]) - 1, parseInt(x[2]));
        nn = parseInt(y.getTime() / 1000);
        now = (new Date().getTime()) / 1000;
        if (nn >= now)
            alert("Date is in the future!")
            return
        
        fetch("addrelease.py?json=true&committee=" + pmc + "&version=" + escape(version) + "&date=" + nn, null,
            (json) ->
                if (json && json.versions)
                    n = 0;
                    for version in json.versions
                        n++;
                        jsdata.releases[pmc][version] = json.versions[version]
                    
                    $('#rdialog_' + pmc).dialog("close")
                    nproject = pmc
                    alert("Release added!")
                    renderFrontPage(jsdata)
                else if (json && json.status)
                    alert(json.status)
                else if (json)
                    alert(JSON.stringify(json))
                else
                    alert("Couldn't add release data :(")
        )

