
currentTab = 0


# Display tabs
loadTabs = (stab) ->
    main = new HTML('div', { id: 'dialog'})
    document.getElementById('wrapper').innerHTML = ""
    document.getElementById('wrapper').appendChild(main)
    
    tdiv = new HTML('div', {class: 'tabs'})
    main.inject(tdiv)
    k = 0
    for v in tabs
        if (stab and stab == k) or (not stab and k == 0)
            currentTab = k
            history.pushState(null, null, "?#{k}")
            tab = new HTML('div', {class: 'tablink tablink_selected'}, v.title)
        else
            tab = new HTML('div', {class: 'tablink', onclick: "loadTabs(" + k + ");"}, v.title)
        tdiv.inject(tab)
        k++
    
    # Check if person is a member of any PMC or an ASF member
    if jsdata.all.length > 0
        bread = new HTML('div', { class: 'bread', id: 'contents'}, "Loading page, please wait...")
        main.inject(bread)
        
        # Dirty hack to determine membership for now
        if jsdata.all.length > 200
            all = ['Add a tab:', '---------------']
            for pmc in jsdata.all or []
                all.push(pmc)
            sel = makeSelect('project', all)
            sel.setAttribute("onchange", "addTab(this.value);")
            tdiv.inject(sel)
            
            
        # If all good, render the tab
        loadBread(stab)
    else
        main.inject(new HTML('p', { class: 'warning'}, "You need to be a member of at least one PMC in order to utilize the reporting tool."))

addTab = (pmc) ->
    fetch("getjson.py?only="+pmc, {pmc: pmc}, preloadTabs)

loadBread = (which) ->
    if tabs[which] and tabs[which].renderer
        # Clear bread div
        document.getElementById('contents').innerHTML = ""
        # Render tab using render function
        tabs[which].renderer(tabs[which].state)
        

