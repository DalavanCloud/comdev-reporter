#!/usr/bin/env python
"""
    CGI script to return data to the Javacript that renders the site (render.js)
    
    It also populates various json files from JIRA if they are stale:
    data/JIRA/projects.json - list of all JIRA projects
    data/JIRA/%.json - for each JIRA project
    
    Usage:
        getjson.py[?only=pmcname]
    
    Reads the following:
        projects.apache.org/site/json/foundation/pmcs.json
        projects.apache.org/site/json/foundation/chairs.json
        projects.apache.org/site/json/projects/%s.json
        data/JIRA/projects.json
        data/JIRA/%s.json
        data/health.json
        data/releases/%s.json
        data/pmcs.json
        data/projects.json
        data/mailinglists.json
        data/maildata_extended.json
        
    
    Environment variables:
    
"""

import os, sys, re, json, subprocess, time
import base64, urllib2, cgi

form = cgi.FieldStorage();
oproject = form['only'].value if ('only' in form and len(form['only'].value) > 0) else os.environ['ONLY'] if 'ONLY' in os.environ else None


jmap = {
    'trafficserver': ['TS'],
    'cordova': ['CB'],
    'corinthia': ['COR']
}

pmap = {# convert mailing list name to PMC name
    'community': 'comdev',
    'ws': 'webservices',
    'hc': 'httpcomponents',
    'whimsical': 'whimsy',
    'empire': 'empire-db'
}

mboxmap = {
    'empire-db': 'empire'
}

ldapmap = {
    'webservices': 'ws'
}

jirapass = ""
with open("/var/www/reporter.apache.org/data/jirapass.txt", "r") as f:
    jirapass = f.read().strip()
    f.close()


def getPMCs(uid):
    """ Reads LDAP and returns the array of committee groups to which the uid belongs
    Excludes incubator"""
    groups = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '(|(memberUid=%s)(member=uid=%s,ou=people,dc=apache,dc=org))' % (uid, uid), 'cn'])
    picked = {}
    for match in re.finditer(r"dn: cn=([-a-zA-Z0-9]+),ou=pmc,ou=committees,ou=groups,dc=apache,dc=org", ldapdata):
        group = match.group(1)
        if group != "incubator":
            groups.append(group)
    return groups


def isMember(uid):
    """Reads LDAP to determine if the uid is a member of the ASF"""
    members = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '-b', 'cn=member,ou=groups,dc=apache,dc=org'])
    for match in re.finditer(r"memberUid: ([-a-z0-9_.]+)", ldapdata):
        group = match.group(1)
        members.append(group)
    if uid in members:
        return True
    return False

def getJIRAProjects(project):
    """Reads data/JIRA/projects.json (re-creating it if it is stale)
       Returns the list of JIRA projects for the project argument
       Assumes that the project names match or the project category matches
       (after trimming "Apache " and spaces and lower-casing)"""
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
                req = urllib2.Request("https://issues.apache.org/jira/rest/api/2/project.json")
                req.add_header("Authorization", "Basic %s" % base64string)
                x = json.loads(urllib2.urlopen(req).read())
                with open("/var/www/reporter.apache.org/data/JIRA/projects.json", "w") as f:
                    json.dump(x, f, indent=1)
                    f.close()
            except:
                pass
    except:
        pass
    
    for entry in x:
        if entry['name'].replace("Apache ", "").strip().lower() == project:
            jiras.append(entry['key'])
        elif 'projectCategory' in entry and fixProjectCategory(entry['projectCategory']['name']) == project:
            jiras.append(entry['key'])
    return jiras

def fixProjectCategory(cat):
    return cat.replace("Apache ", "").replace(" Framework", "").strip().lower()

def getJIRAS(project):
    """Reads data/JIRA/%s.json % (project), re-creating it if it is stale
       from the number of issues created and resolved in the last 91 days
       Returns array of [created, resolved, project]
    """
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
            req = urllib2.Request("""https://issues.apache.org/jira/rest/api/2/search?jql=project%20=%20'""" + project + """'%20AND%20created%20%3E=%20-91d""")
            req.add_header("Authorization", "Basic %s" % base64string)
            cdata = json.loads(urllib2.urlopen(req).read())
            req = urllib2.Request("""https://issues.apache.org/jira/rest/api/2/search?jql=project%20=%20'""" + project + """'%20AND%20resolved%20%3E=%20-91d""")
            req.add_header("Authorization", "Basic %s" % base64string)
            rdata = json.loads(urllib2.urlopen(req).read())
            with open("/var/www/reporter.apache.org/data/JIRA/%s.json" % project, "w") as f:
                json.dump([cdata['total'], rdata['total'], project], f, indent=1)
                f.close()
            return cdata['total'], rdata['total'], project
        except Exception as err:
            with open("/var/www/reporter.apache.org/data/JIRA/%s.json" % project, "w") as f:
                json.dump([0,0,None], f, indent=1)
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
    """Reads data/releases/%s.json and returns the contents"""
    try:
        with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "r") as f:
            x = json.loads(f.read())
            f.close()
        return x;
    except:
        return {}


user = os.environ['HTTP_X_AUTHENTICATED_USER'] if 'HTTP_X_AUTHENTICATED_USER' in os.environ else ""
m = re.match(r"^([-a-zA-Z0-9_.]+)$", user)

if m:
    pchanges = {}
    cchanges = {}
    with open("/var/www/reporter.apache.org/data/pmcs.json", "r") as f:
        pchanges = json.loads(f.read())
        f.close()
    
    with open("/var/www/reporter.apache.org/data/projects.json", "r") as f:
        cchanges = json.loads(f.read())
        f.close()
    bugzillastats = {}
    try:
        with open("/var/www/reporter.apache.org/data/bugzillastats.json", "r") as f:
            bugzillastats = json.loads(f.read())
            f.close()
    except:
        pass
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
        for entry in ml: # e.g. abdera.apache.org-commits, ws.apache.org-dev
            tlp = entry.split(".")[0]
            if tlp in pmap: # convert ml prefix to PMC internal name
                tlp = pmap[tlp]
            if tlp in groups:
                mlstats[tlp] = mlstats[tlp] if tlp in mlstats else {}
                mlstats[tlp][entry] = ml[entry]
    emails = {}
    pmcdates = {}
    with open("/var/www/reporter.apache.org/data/maildata_extended.json", "r") as f:
        mld = json.loads(f.read())
        f.close()
        for entry in mld: # e.g. hc-dev, ant-users, ws-dev
            tlp = entry.split("-")[0]
            nentry = entry
            if tlp == "empire":
                tlp = "empire-db"
                nentry = entry.replace("empire-", "empire-db-")
            if tlp in pmap: # convert ml prefix to PMC internal name
                tlp = pmap[tlp]
            if tlp in groups:
                emails[tlp] = emails[tlp] if tlp in emails else {}
                emails[tlp][nentry] = mld[entry]
    with open("/var/www/reporter.apache.org/data/pmcdates.json", "r") as f:
        pmcdates = json.loads(f.read())
        f.close()
    dates = {}
    bdata = {} # bugzilla data
    jdata = {}
    cdata = {}
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
        ddata[group], allpmcs, health[group] = getProjectData(group)
        rdata[group] = getReleaseData(group)
        if group in bugzillastats:
            bdata[group] = bugzillastats[group]
        else:
            bdata[group] = [0,0,{}]
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
        if group in pmcdates: # Make sure we have this PMC in the JSON, so as to not bork
            dates[group] = pmcdates[group] # only send the groups we want
    if not isMember(uid):
        allpmcs = []
    output = {
        'count': count,
        'pmcs': groups,
        'all': allpmcs,
        'mail': mlstats,
        'delivery': emails,
        'jira': jdata,
        'bugzilla': bdata,
        'changes': cdata,
        'dates': dates,
        'pdata': ddata,
        'releases': rdata,
        'keys': keys,
        'health': health
    }
    dump = json.dumps(output, indent=1)
    print ("Content-Type: application/json\r\nContent-Length: %u\r\n\r\n" % (len(dump)+1))
    print(dump)
else:
    print ("Content-Type: text/html\r\n\r\n")
    print("Unknown or invalid user id presented")
