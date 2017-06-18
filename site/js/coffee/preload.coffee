

# Tabs above in the menu
tabs = [
    
]

jsdata = {}

mergeData = (json, pmc) ->
    if not pmc
        jsdata = json
        return
    if pmc in jsdata.pmcs
        return
    if (nproject && nproject.length > 0)
        for xpmc, i in jsdata.pmcs
            if (xpmc == nproject)
                jsdata.pmcs.splice(i, 1);
                break
            
    todo = new Array('count', 'mail', 'delivery', 'bugzilla', 'jira', 'changes', 'pmcdates', 'pdata', 'releases', 'keys', 'health')
    for key, i in todo
        jsdata[key][pmc] = json[key][pmc];
    jsdata.pmcs.push(pmc)
    nproject = pmc


preloadTabs = (json, state) ->
    cpmc = if isHash(state) and state.pmc then state.pmc else null
    mergeData(json, cpmc)
    tabs = []
    a = 0
    ctab = 0
    for pmc in jsdata.pmcs
        tab = {
            id: pmc,
            title: pmc,
            renderer: renderFrontPage,
            state: pmc
        }
        tabs.push(tab)
        if cpmc == pmc
            ctab = a
        a++
    loadTabs(ctab)


