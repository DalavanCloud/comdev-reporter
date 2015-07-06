#!/usr/bin/env python

import re, os, json, urllib2, base64, time
from os import listdir
from os.path import isfile, join

mypath = "/var/www/reporter.apache.org/data/JIRA"
myfiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]

jirapass = ""
with open("/var/www/reporter.apache.org/data/jirapass.txt", "r") as f:
    jirapass = f.read().strip()
    f.close()
    
def getJIRAS(project):
    refresh = True
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

for project in myfiles:
    jiraname = project.replace(".json", "")
    if jiraname != "projects":
        print("Refreshing JIRA stats for " + jiraname)
        getJIRAS(jiraname)
        time.sleep(2)
    