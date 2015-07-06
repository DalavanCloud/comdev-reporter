#!/usr/bin/env python
import os, sys, json, urllib2, re, time, base64, cgi, subprocess

form = cgi.FieldStorage();
user = os.environ['HTTP_X_AUTHENTICATED_USER'] if 'HTTP_X_AUTHENTICATED_USER' in os.environ else "nobody"
project = form['project'].value if ('project' in form and len(form['project'].value) > 0) else None
jiraname = form['jiraname'].value if ('jiraname' in form and len(form['jiraname'].value) > 0) else None
prepend = form['prepend'].value if ('prepend' in form and len(form['prepend'].value) > 0) else None
    
def getPMCs(uid):
    groups = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '(|(memberUid=%s)(member=uid=%s,ou=people,dc=apache,dc=org))' % (uid, uid), 'cn'])
    picked = {}
    for match in re.finditer(r"dn: cn=([a-zA-Z0-9]+),ou=pmc,ou=committees,ou=groups,dc=apache,dc=org", ldapdata):
        group = match.group(1)
        if group != "incubator":
            
            groups.append(group)
    return groups


def getReleaseData(project):
    try:
        with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "r") as f:
            x = json.loads(f.read())
            f.close()
        return x;
    except:
        return {}


def isMember(uid):
    members = []
    ldapdata = subprocess.check_output(['ldapsearch', '-x', '-LLL', '-b', 'cn=member,ou=groups,dc=apache,dc=org'])
    for match in re.finditer(r"memberUid: ([-a-z0-9_.]+)", ldapdata):
        group = match.group(1)
        members.append(group)
    if uid in members:
        return True
    return False


jirapass = ""
with open("/var/www/reporter.apache.org/data/jirapass.txt", "r") as f:
    jirapass = f.read().strip()
    f.close()

groups = getPMCs(user)
if (isMember(user) or project in groups)  and jiraname:
       jiraname = jiraname.upper()
       base64string = base64.encodestring('%s:%s' % ('githubbot', jirapass))[:-1]
       rdata = getReleaseData(project)
       try:
           req = req = urllib2.Request("https://issues.apache.org/jira/rest/api/2/project/%s/versions" % jiraname)
           req.add_header("Authorization", "Basic %s" % base64string)
           cdata = json.loads(urllib2.urlopen(req).read())
           for entry in cdata:
              if ('name' in entry and 'releaseDate' in entry and 'released' in entry and entry['released']):
                     date = time.mktime(time.strptime(entry['releaseDate'], "%Y-%m-%d"))
                     if prepend:
                        entry['name'] = "%s-%s" % (prepend, entry['name'])
                     rdata[entry['name']] = date
       except Exception as err:
           pass
       with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "w") as f:
              f.write(json.dumps(rdata))
              f.close()
              
       print("Content-Type: application/json\r\n\r\n")
       print(json.dumps({'status': 'Fetched', 'versions': rdata}))
    
else:
       print("Content-Type: application/json\r\n\r\n{\"status\": \"Data missing\"}\r\n")
