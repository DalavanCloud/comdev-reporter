
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
            title = new HTML('h2', {}, v.title+":")
            main.inject(title)
        else
            tab = new HTML('div', {class: 'tablink', onclick: "loadTabs(" + k + ");"}, v.title)
        tdiv.inject(tab)
        k++
    
    all = ['Add a tab:', '---------------']
    for pmc in jsdata.all or []
        all.push(pmc)
    sel = makeSelect('project', all)
    sel.setAttribute("onchange", "addTab(this.value);")
    tdiv.inject(sel)
    bread = new HTML('div', { class: 'bread', id: 'contents'})
    main.inject(bread)
    loadBread(stab)

addTab = (pmc) ->
    fetch("getjson.py?only="+pmc, {pmc: pmc}, preloadTabs)

loadBread = (which) ->
    if tabs[which] and tabs[which].renderer
        # Clear bread div
        document.getElementById('contents').innerHTML = ""
        # Render tab using render function
        tabs[which].renderer(tabs[which].state)
        

