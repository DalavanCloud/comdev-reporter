import os, sys, json, urllib2, re, time, base64

def getReleaseData(project):
    try:
        with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "r") as f:
            x = json.loads(f.read())
            f.close()
        return x;
    except:
        return {}
       
projects = {
       'trafficserver': 'TS',
       'accumulo': 'ACCUMULO'
}

jirapass = ""
with open("/var/www/reporter.apache.org/data/jirapass.txt", "r") as f:
    jirapass = f.read().strip()
    f.close()

for project in projects:
       jiraname = projects[project]
       base64string = base64.encodestring('%s:%s' % ('githubbot', jirapass))[:-1]
       rdata = getReleaseData(project)
       try:
           req = req = urllib2.Request("https://issues.apache.org/jira/rest/api/2/project/%s/versions" % jiraname)
           req.add_header("Authorization", "Basic %s" % base64string)
           cdata = json.loads(urllib2.urlopen(req).read())
           for entry in cdata:
              if ('name' in entry and 'releaseDate' in entry and 'released' in entry and entry['released']):
                     
                     date = time.mktime(time.strptime(entry['releaseDate'], "%Y-%m-%d"))
                     print("Updating version for %s - %s: %u" % (project, entry['name'], date))
                     rdata[entry['name']] = date
       except Exception as err:
           print(err)
       
       with open("/var/www/reporter.apache.org/data/releases/%s.json" % project, "w") as f:
              f.write(json.dumps(rdata))
              f.close()