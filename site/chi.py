#!/usr/bin/env python
import os, re, json, time
import cgi

import sys
sys.path.append("../scripts") # module is in sibling directory
import committee_info

form = cgi.FieldStorage();
oproject = form['only'].value if ('only' in form and len(form['only'].value) > 0) else None

pmap = {
    'community': 'comdev',
    'ws': 'webservices',
    'hc': 'httpcomponents',
    'whimsical': 'whimsy',
    'empire': 'empire-db'
}

ldapmap = {
    'webservices': 'ws'
}

def getReleaseData(project):
    try:
        with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "r") as f:
            x = json.loads(f.read())
            f.close()
        return x;
    except:
        return {}



pchanges = {}
cchanges = {}

with open("/var/www/reporter.apache.org/data/pmcs.json", "r") as f:
    pchanges = json.loads(f.read())
    f.close()

with open("/var/www/reporter.apache.org/data/projects.json", "r") as f:
    cchanges = json.loads(f.read())
    f.close()


user = os.environ['HTTP_X_AUTHENTICATED_USER'] if 'HTTP_X_AUTHENTICATED_USER' in os.environ else ""
m = re.match(r"^([-a-zA-Z0-9_.]+)$", user)
groups = []

afterQuarter = time.time() - (3*31*86400)
afterHalf = time.time() - (6*31*86400)
afterFull = time.time() - (12*31*86400)
cdata = {}
if m:
    uid = m.group(1)
    if uid:
        mlstats = {} # Does not appear to be used
        with open("/var/www/reporter.apache.org/data/mailinglists.json", "r") as f:
            ml = json.loads(f.read())
            f.close()
            for entry in ml:
                tlp = entry.split(".")[0] # e.g. lucene.apache.org-general => lucene
                if tlp in pmap:
                    tlp = pmap[tlp]
                if True:
                    mlstats[tlp] = mlstats[tlp] if tlp in mlstats else {}
                    mlstats[tlp][entry] = ml[entry]
        emails = {}
        with open("/var/www/reporter.apache.org/data/maildata_extended.json", "r") as f:
            mld = json.loads(f.read())
            f.close()
            for entry in mld:
                tlp = entry.split("-")[0]
                if tlp in pmap:
                    tlp = pmap[tlp]
                nentry = entry
                if tlp == "empire":
                    tlp = "empire-db"
                    nentry = entry.replace("empire-", "empire-db-")
                if True:
                    emails[tlp] = emails[tlp] if tlp in emails else {}
                    emails[tlp][nentry] = mld[entry]
        jdata = {}
        rdata = {}
        keys = {}
        count = {}
        pmcnames = committee_info.PMCnames()
        npmcs = {}
        ncoms = {}
        names = {}
        
        for group in pmcnames:
            jiras = []
            count[group] = [0,0]
            xgroup = group
            if group in ldapmap:
                xgroup = ldapmap[group]
            if xgroup in pchanges:
                count[group][0] = len(pchanges[xgroup])
            if xgroup in cchanges:
                count[group][1] = len(cchanges[xgroup])
            names[group] = pmcnames[group]
            rdata[group] = getReleaseData(group) 
            cdata[group] = cdata[xgroup] if xgroup in cdata else {'pmc': {}, 'committer': {}}
            
            for pmc in pchanges:
                if pmc == xgroup:
                    for member in pchanges[pmc]:
                        if pchanges[pmc][member][1] > 0:
                            cdata[group]['pmc'][member] = pchanges[pmc][member]
                            npmcs[group] = npmcs[group] if (group in npmcs and npmcs[group] > pchanges[pmc][member][1]) else pchanges[pmc][member][1]
            for pmc in cchanges:
                if pmc == xgroup:
                    for member in cchanges[pmc]:
                        if cchanges[pmc][member][1] > 0:
                            cdata[group]['committer'][member] = cchanges[pmc][member]
                            ncoms[group] = ncoms[group] if (group in ncoms and ncoms[group] > cchanges[pmc][member][1]) else cchanges[pmc][member][1]
        
        notes = []
        status = [0,0,0,0,0,0]
        for group in sorted(pmcnames):
            if group == "xmlbeans":
                continue
            x = 0
            y = 0
            score = 0
            note = []
            if group in emails:
                for entry in emails[group]:
                    x += emails[group][entry]['quarterly'][0]
                    y += emails[group][entry]['quarterly'][1]
            if x == 0:
                score += 2.5
                note.append("No email sent to ANY ML in the past quarter (-2.50&#27683;)")
            elif x < 4:
                score += 2.25
                note.append("Less than one email per month to all MLs combined in the past quarter (-2.25&#27683;)")
            elif x < 14:
                score += 1.75
                note.append("Less than one email per week to all MLs combined in the past quarter (-1.75&#27683;)")
            elif x < 45:
                score += 1.5
                note.append("Less than one email per 2 days to all MLs combined in the past quarter (-1.50&#27683;)")
            elif x < 92:
                score += 1
                note.append("Less than one email per day to all MLs combined in the past quarter (-1.00&#27683;)")
            elif x < 184:
                score += 0.5
                note.append("Less than two emails per day to all MLs combined in the past quarter (-0.50&#27683;)")
            elif x < 368:
                score -= 0.5
                note.append("More than 2 emails per day to all MLs combined in the past quarter (+0.50&#27683;)")
            elif x >= 368:
                score -= 1
                note.append("More than 4 emails per day to all MLs combined in the past quarter (+1.00&#27683;)")
            if (x+y) < 7:
                score += 2
                note.append("Less than one email per month sent to all MLs combined in the last six months (-2.00&#27683;)")
            elif y < 14 and x < 14:
                score += 1.75
                note.append("Less than one email per week to all MLs combined in the past six months (-1.75&#27683;)")
            elif y < 45 and x < 45:
                score += 1.5
                note.append("Less than one email per 2 days to all MLs combined in the past six months (-1.50&#27683;)")
            elif y < 90 and x < 90:
                score += 1
                note.append("Less than one email per day to all MLs combined in the past six months (-1.00&#27683;)")
            if group in rdata:
                tooold = True if len(rdata[group]) > 0 else False
                tooold2 = True if len(rdata[group]) > 0 else False
                for version in rdata[group]:
                    if rdata[group][version] > afterFull:
                        tooold = False
                    if rdata[group][version] > (time.time() - (31536000*2)):
                        tooold2 = False
                if tooold2:
                    score += 1.5
                    note.append("No releases in the last 2+ years (-1.50&#27683;)")
                elif tooold:
                    score += 1
                    note.append("No releases in the last year (-1.00&#27683;)")
                
                if len(rdata[group]) == 0:
                    score += 0.5
                    note.append("No release data available! (-0.50&#27683;)")
            if group in npmcs:
                if npmcs[group] < afterFull:
                    score += 1
                    note.append("No new members added to the LDAP committee group for more than a year (-1.00&#27683;)")
                elif npmcs[group] < afterHalf:
                    score += 0.5
                    note.append("No new members added to the LDAP committee group for more than six months (-0.50&#27683;)")
                else:
                    score -= 0.5
                    note.append("New members() added to the LDAP committee group within the last six months (+0.50&#27683;)")
            elif group != "bookkeeper":
                score += 2
                note.append("No new members added to the LDAP committee group for more than 2 years (-2.00&#27683;)")
                
            if group in ncoms:
                if ncoms[group] < afterFull:
                    score += 1
                    note.append("No new committers invited for more than a year (-1.00&#27683;)")
                elif ncoms[group] < afterHalf:
                    score += 0.5
                    note.append("No new committers invited for more than six months (-0.50&#27683;)")
                elif ncoms[group] < afterQuarter:
                    score -= 0.5
                    note.append("New committer(s) invited within the last six months (+0.50&#27683;)")
                else:
                    score -= 0.75
                    note.append("New committer(s) invited within the last three months (+0.75&#27683;)")
            elif group != "bookkeeper":
                score += 2
                note.append("No new committers invited for more than 2 years (-2.00&#27683;)")
                
            s = int(score/1.80)
            if s > 4:
                s = 4
            s = s + 1
            if s < 0:
                s = 0
            notes.append ({
                'pmc': names[group] if (group in names) else group,
                'score': score,
                'notes': note,
                'group': group,
                'cscore': s
            })
        with open("/var/www/reporter.apache.org/data/health.json", "w") as f:
            json.dump(notes, f, indent=1, sort_keys=True)
            f.close()
            
        print ("Content-Type: text/html\r\n\r\n<h1><img src='/img/chi.png' style='vertical-align: middle;'/> Community Health Issues</h1><p>This is a quantitative guideline only. There may be niche cases where the summaries below to not apply. <br/>Scores range from -10.00 (worst possible score) to +10.00 (best possible score), harmonized by <img src='/img/equation.png' style='vertical-align: middle;'/></p>")
        values = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
        xvalues = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
        colors = ["#000070", "#007000", "#407000", "#70500", "#700000", "#A00000"]
        for entry in sorted(notes, key=lambda x: x['score'], reverse=True):
            s = int(entry['score']/1.80)
            if s > 4:
                s = 4
            s = s + 1
            if s < 0:
                s = 0
            status[s] += 1;
        
        y = 0
        for s in status:
            xvalues[y] = "%s (%u)" % (values[y], s)
            y += 1
        print('<img src="https://chart.googleapis.com/chart?cht=p&amp;chs=640x260&amp;chd=t:%s&amp;chl=%s&amp;chco=0000A0|00A000|A0D000|F0D000|F08500|A00000"/><br/><br/>' % ( ",".join(str(x) for x in status), "|".join(xvalues)))
              
        for entry in sorted(sorted(notes, key=lambda x: x['group']), key=lambda x: x['score'], reverse=True):
            s = int(entry['score']/1.80)
            if s > 4:
                s = 4
            s = s + 1
            if s < 0:
                s = 0
            status[s] += 1;
            print("<font color='%s'>\r" % colors[s])
            print( "<b id='%s'>%s%s: %s%s</b><br/>\r" % (entry['group'], "<u>" if s >= 4 else "", entry['pmc'], values[s],"</u>" if s >= 4 else "",  ))
            print( "<blockquote><b>Health score:</b> %0.2f<br>\r" % (6.33+((-1 * entry['score'])* (20/12.25))))
            for l in entry['notes']:
                print("<b>Score note: </b>%s<br/>\r" % l)
            print("</blockquote></font><hr/>\r")
            
    else:
        print ("Content-Type: text/html\r\n\r\n")
        print("Unknown or invalid member id presented")
else:
    print ("Content-Type: text/html\r\n\r\n")
    print("Unknown or invalid user id presented")
