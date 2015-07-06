#!/usr/bin/env python
import os, sys, re, json, subprocess, urllib, time
import base64, urllib2, cgi

form = cgi.FieldStorage();
oproject = form['only'].value if ('only' in form and len(form['only'].value) > 0) else None


jmap = {
    'trafficserver': ['TS'],
    'cordova': ['CB'],
    'corinthia': ['COR']
}

pmap = {
    'community': 'comdev',
    'ws': 'webservices'
}

ldapmap = {
    'webservices': 'ws'
}

jirapass = ""
with open("/var/www/reporter.apache.org/data/jirapass.txt", "r") as f:
    jirapass = f.read().strip()
    f.close()

def isMember(uid):
    members = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '-b', 'cn=member,ou=groups,dc=apache,dc=org'])
    for match in re.finditer(r"memberUid: ([-a-z0-9_.]+)", ldapdata):
        group = match.group(1)
        members.append(group)
    if uid in members:
        return True
    return False


def getProjectData(project):
    try:
        y = []
        with open("/var/www/projects.apache.org/site/json/projects/%s.json" % project, "r") as f:
            x = json.loads(f.read())
            f.close()
            with open("/var/www/projects.apache.org/site/json/foundation/pmcs.json", "r") as f:
                p = json.loads(f.read())
                f.close()
                for xproject in p:
                    y.append(xproject)
                    if xproject == project:
                        x['name'] = p[project]['name']
            with open("/var/www/projects.apache.org/site/json/foundation/chairs.json", "r") as f:
                c = json.loads(f.read())
                f.close()
                for xproject in c:
                    if xproject.lower() == x['name'].lower():
                        x['chair'] = c[xproject]

        return x, y;
    except:
        x = {}
        y = []
        with open("/var/www/projects.apache.org/site/json/foundation/pmcs.json", "r") as f:
            p = json.loads(f.read())
            f.close()
            for xproject in p:
                y.append(xproject)
                if xproject == project:
                    x['name'] = p[project]['name']

        with open("/var/www/projects.apache.org/site/json/foundation/chairs.json", "r") as f:
            c = json.loads(f.read())
            f.close()
            for xproject in c:
                if 'name' in x and xproject == x['name']:
                    x['chair'] = c[xproject]
        return x,y

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

afterHalf = time.time() - (6*31*86400)
afterFull = time.time() - (12*31*86400)
cdata = {}
if m:
    uid = m.group(1)
    if isMember(uid):
        mlstats = {}
        with open("/var/www/reporter.apache.org/data/mailinglists.json", "r") as f:
            ml = json.loads(f.read())
            f.close()
            for entry in ml:
                tlp = entry.split(".")[0]
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
                if True:
                    emails[tlp] = emails[tlp] if tlp in emails else {}
                    emails[tlp][entry] = mld[entry]
        jdata = {}
        ddata = {}
        rdata = {}
        allpmcs = []
        keys = {}
        count = {}
        foo, allpmcs = getProjectData('httpd')
        npmcs = {}
        ncoms = {}
        for group in allpmcs:
            jiras = []
            count[group] = [0,0]
            xgroup = group
            if group in ldapmap:
                xgroup = ldapmap[group]
            if xgroup in pchanges:
                count[group][0] = len(pchanges[xgroup])
            if xgroup in cchanges:
                count[group][1] = len(cchanges[xgroup])
            ddata[group], bleh = getProjectData(group)
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
        for group in allpmcs:
            x = 0
            y = 0
            score = 0
            note = []
            if group in emails:
                for entry in emails[group]:
                    x += emails[group][entry]['quarterly'][0]
                    y += emails[group][entry]['quarterly'][1]
            if x < 90:
                score += 1
                note.append("Less than one email per day to all MLs in the past quarter")
            if y < 90 and x < 90:
                score += 1
                note.append("Less than one email per day to all MLs in the past six months")
            if group in rdata:
                tooold = True if len(rdata[group]) > 0 else False
                for version in rdata[group]:
                    if rdata[group][version] > afterFull:
                        tooold = False
                if tooold:
                    score += 1
                    note.append("No releases in the last year")
                if len(rdata[group]) == 0:
                    score += 0.5
                    note.append("No release data available!")
            if group in npmcs:
                if npmcs[group] < afterFull:
                    score += 1
                    note.append("No new PMC members invited for more than a year")
            elif group != "bookkeeper":
                score += 2
                note.append("No new PMC members invited for more than 2 years")
                
            if group in ncoms:
                if ncoms[group] < afterFull:
                    score += 1
                    note.append("No new committers invited for more than a year")
            elif group != "bookkeeper":
                score += 2
                note.append("No new committers invited for more than 2 years")
                
            notes.append ({
                'pmc': group,
                'score': score,
                'notes': note
            })
        
        print ("Content-Type: text/html\r\n\r\n<h2>Community health issues</h2>")
        values = ["Healthy", "Mostly Okay", "Unhealthy", "Action required!"]
        colors = ["#070", "#470", "#770", "#700"]
        for entry in sorted(notes, key=lambda x: x['score'], reverse=True):
            s = int(entry['score']/2)
            if s > 3:
                s = 3
            print("<font color='%s'>" % colors[s])
            print "<b>%s: %s</b><br/>\n" % (entry['pmc'], values[s] )
            print "<blockquote><b>Health score:</b> %u<br>" % (-1 * entry['score'])
            for l in entry['notes']:
                print("<b>Problem: </b>%s<br/>" % l)
            print("</blockquote></font><hr/>\n")
            
    else:
        print ("Content-Type: text/html\r\n\r\n")
        print("Unknown or invalid member id presented")
else:
    print ("Content-Type: text/html\r\n\r\n")
    print("Unknown or invalid user id presented")
