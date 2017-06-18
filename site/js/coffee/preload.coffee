

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
    todo = new Array('count', 'mail', 'delivery', 'bugzilla', 'jira', 'changes', 'pmcdates', 'pdata', 'releases', 'keys', 'health')
    for key in todo
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
        if jsdata.pdata[pmc] and jsdata.pdata[pmc].chair # Require this to show a tab
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


