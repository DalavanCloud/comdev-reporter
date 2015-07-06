import sys
# The code uses urllib.request which is Python3
if sys.hexversion < 0x030000F0:
    raise RuntimeError("This script requires Python3")

import re
import urllib.request
import csv
import json
import os
import datetime
import time
pmcs = {}
try:
    with open("pmcs.json", "r") as f:
        pmcs = json.loads(f.read())
        f.close()
except:
    pass

projects = {}
try:
    with open("projects.json", "r") as f:
        projects = json.loads(f.read())
        f.close()
except:
    pass


people = {}
newgroups = []

data = urllib.request.urlopen("http://people.apache.org/committer-index.html").read().decode('utf-8')
x = 0
for committer in re.findall(r"<tr>([\S\s]+?)</tr>", data, re.MULTILINE | re.UNICODE):
    x += 1
##    print(committer)
    m = re.search(r"<a id='(.+?)'>[\s\S]+?<td.+?>\s*(.+?)</td>[\s\S]+?>(.+)</td>", committer, re.MULTILINE | re.UNICODE)
    if m:
        cid = m.group(1)
        cname = re.sub(r"<.+?>", "", m.group(2), 4)
        cproj = m.group(3)
        isMember = False
        if re.search(r"<b", committer, re.MULTILINE | re.UNICODE):
            isMember = True
        for project in re.findall(r"#([-a-z0-9._]+)-pmc", cproj):
            now = time.time()
            if not project in pmcs:
                pmcs[project] = {}
                newgroups.append(project)
            if project in newgroups:
                now = 0
            if not cid in pmcs[project]:
                pmcs[project][cid] = [cname, now, time.time()]
            else:
                pmcs[project][cid] = [pmcs[project][cid][0], pmcs[project][cid][1], time.time()]
                
        for project in re.findall(r"#([-a-z0-9._]+)(?!-pmc)", cproj):
            now = time.time()
            if not project in projects:
                projects[project] = {}
                newgroups.append(project)
            elif project in newgroups:
                now = 0
            if not cid in projects[project]:
                projects[project][cid] = [cname, now, time.time()]
            else:
                projects[project][cid] = [projects[project][cid][0], projects[project][cid][1], time.time()]
    
# Delete retired members
ret = 0
for project in projects:
    for cid in projects[project]:
        if len(projects[project][cid]) < 3 or projects[project][cid][2] < (time.time() - (86400*3)):
            projects[project][cid] = "!"
    projects[project] =  {i:projects[project][i] for i in projects[project] if projects[project][i]!="!"}

for project in pmcs:
    for cid in pmcs[project]:
        if len(pmcs[project][cid]) < 3 or pmcs[project][cid][2] < (time.time() - (86400*3)):
            pmcs[project][cid] = "!"
    pmcs[project] =  {i:pmcs[project][i] for i in pmcs[project] if pmcs[project][i]!="!"}

    
print("Writing pmcs.json")
with open("pmcs.json", "w") as f:
    f.write(json.dumps(pmcs))
    f.close()

print("Writing projects.json")
with open("projects.json", "w") as f:
    f.write(json.dumps(projects))
    f.close()
    
    
print("All done! removed %u retired entries" % ret)

