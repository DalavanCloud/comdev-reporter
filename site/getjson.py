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

def getPMCs(uid):
    groups = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '(|(memberUid=%s)(member=uid=%s,ou=people,dc=apache,dc=org))' % (uid, uid), 'cn'])
    picked = {}
    for match in re.finditer(r"dn: cn=([a-zA-Z0-9]+),ou=pmc,ou=committees,ou=groups,dc=apache,dc=org", ldapdata):
        group = match.group(1)
        if group != "incubator":

            groups.append(group)
    return groups


def isMember(uid):
    members = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '-b', 'cn=member,ou=groups,dc=apache,dc=org'])
    for match in re.finditer(r"memberUid: ([-a-z0-9_.]+)", ldapdata):
        group = match.group(1)
        members.append(group)
    if uid in members:
        return True
    return False

def getJIRAProjects(project):
    project = project.replace("Apache ", "").strip().lower()
    refresh = True
    x = {}
    jiras = []
    try:
        mtime = 0
        try:
            st=os.stat("/var/www/reporter.apache.org/data/JIRA/projects.json")
            mtime=st.st_mtime
        except:
            pass
        if mtime >= (time.time() - 86400):
            refresh = False
            with open("/var/www/reporter.apache.org/data/JIRA/projects.json", "r") as f:
                x = json.loads(f.read())
                f.close()
        else:
            base64string = base64.encodestring('%s:%s' % ('githubbot', jirapass))[:-1]
    
            try:
                req = req = urllib2.Request("https://issues.apache.org/jira/rest/api/2/project.json")
                req.add_header("Authorization", "Basic %s" % base64string)
                x = json.loads(urllib2.urlopen(req).read())
                with open("/var/www/reporter.apache.org/data/JIRA/projects.json", "w") as f:
                    f.write(json.dumps(x))
                    f.close()
            except:
                pass
    except:
        pass
    
    for entry in x:
        if entry['name'].replace("Apache ", "").strip().lower() == project:
            jiras.append(entry['key'])
        elif 'projectCategory' in entry and entry['projectCategory']['name'].replace("Apache ", "").strip().lower() == project:
            jiras.append(entry['key'])
    return jiras

def getJIRAS(project):
    refresh = True
    try:
        st=os.stat("/var/www/reporter.apache.org/data/JIRA/%s.json" % project)
        mtime=st.st_mtime
        if mtime >= (time.time() - (2*86400)):
            refresh = False
            with open("/var/www/reporter.apache.org/data/JIRA/%s.json" % project, "r") as f:
                x = json.loads(f.read())
                f.close()
                return x[0], x[1], x[2]
    except:
        pass

    if refresh:
        base64string = base64.encodestring('%s:%s' % ('githubbot', jirapass))[:-1]

        try:
            req = req = urllib2.Request("""https://issues.apache.org/jira/rest/api/2/search?jql=project%20=%20""" + project + """%20AND%20created%20%3E=%20-91d""")
            req.add_header("Authorization", "Basic %s" % base64string)
            cdata = json.loads(urllib2.urlopen(req).read())
            req = req = urllib2.Request("""https://issues.apache.org/jira/rest/api/2/search?jql=project%20=%20""" + project + """%20AND%20resolved%20%3E=%20-91d""")
            req.add_header("Authorization", "Basic %s" % base64string)
            rdata = json.loads(urllib2.urlopen(req).read())
            with open("/var/www/reporter.apache.org/data/JIRA/%s.json" % project, "w") as f:
                f.write(json.dumps([cdata['total'], rdata['total'], project]))
                f.close()
            return cdata['total'], rdata['total'], project
        except Exception as err:
            with open("/var/www/reporter.apache.org/data/JIRA/%s.json" % project, "w") as f:
                f.write(json.dumps([0,0,None]))
                f.close()
            return 0,0, None

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
        z = {}
        with open("/var/www/reporter.apache.org/data/health.json", "r") as f:
            h = json.loads(f.read())
            f.close()
            z = {}
            for entry in h:
                if entry['group'] == project:
                    z = entry
                    
        return x, y, z;
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
        z = {}
        with open("/var/www/reporter.apache.org/data/health.json", "r") as f:
            h = json.loads(f.read())
            f.close()
            z = {}
            for entry in h:
                if entry['group'] == project:
                    z = entry
        return x,y,z

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

cdata = {}
if m:
    uid = m.group(1)
    groups = getPMCs(uid)
    include = os.environ['QUERY_STRING'] if 'QUERY_STRING' in os.environ else None
    if include and isMember(uid) and not include in groups and len(include) > 1:
        groups.append(include)
    if oproject and len(oproject) > 0 and isMember(uid):
        groups = [oproject]
    mlstats = {}
    with open("/var/www/reporter.apache.org/data/mailinglists.json", "r") as f:
        ml = json.loads(f.read())
        f.close()
        for entry in ml:
            tlp = entry.split(".")[0]
            if tlp in pmap:
                tlp = pmap[tlp]
            if tlp in groups:
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
            if tlp in groups:
                emails[tlp] = emails[tlp] if tlp in emails else {}
                emails[tlp][entry] = mld[entry]
    jdata = {}
    ddata = {}
    rdata = {}
    allpmcs = []
    keys = {}
    count = {}
    health = {}
    for group in groups:
        jiras = []
        count[group] = [0,0]
        xgroup = group
        if group in ldapmap:
            xgroup = ldapmap[group]
        if xgroup in pchanges:
            count[group][0] = len(pchanges[xgroup])
        if xgroup in cchanges:
            count[group][1] = len(cchanges[xgroup])
        jdata[group] = [0,0, None]
        ddata[group], allpmcs, phealth = getProjectData(group)
        health[group] = phealth
        rdata[group] = getReleaseData(group)
        jiraname = group.upper()
        if group in jmap:
            for jiraname in jmap[group]:
                x,y, p = getJIRAS(jiraname)
                jdata[group][0] += x
                jdata[group][1] += y
                jdata[group][2] = p
        elif group in ddata and 'name' in ddata[group]:
            jiras = getJIRAProjects(ddata[group]['name'])
            keys[group] = jiras
            for jiraname in jiras:
                x,y, p= getJIRAS(jiraname)
                jdata[group][0] += x
                jdata[group][1] += y
                jdata[group][2] = p
        elif jiraname:
            x,y, p= getJIRAS(jiraname)
            jdata[group][0] += x
            jdata[group][1] += y
            jdata[group][2] = p

        cdata[group] = cdata[xgroup] if xgroup in cdata else {'pmc': {}, 'committer': {}}
        for pmc in pchanges:
            if pmc == xgroup:
                for member in pchanges[pmc]:
                    if pchanges[pmc][member][1] > 0:
                        cdata[group]['pmc'][member] = pchanges[pmc][member]
        for pmc in cchanges:
            if pmc == xgroup:
                for member in cchanges[pmc]:
                    if cchanges[pmc][member][1] > 0:
                        cdata[group]['committer'][member] = cchanges[pmc][member]
    if not isMember(uid):
        allpmcs = []
    output = {
        'count': count,
        'pmcs': groups,
        'all': allpmcs,
        'mail': mlstats,
        'delivery': emails,
        'jira': jdata,
        'changes': cdata,
        'pdata': ddata,
        'releases': rdata,
        'keys': keys,
        'health': health
    }
    dump = json.dumps(output)
    print ("Content-Type: application/json\r\nContent-Length: %u\r\n\r\n" % (len(dump)+1))
    print(dump)
else:
    print ("Content-Type: text/html\r\n\r\n")
    print("Unknown or invalid user id presented")
