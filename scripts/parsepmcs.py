import sys
# The code uses urllib.request which is Python3
if sys.hexversion < 0x030000F0:
    raise RuntimeError("This script requires Python3")
"""
   This script
   reads: http://people.apache.org/committer-index.html 
   and updates:
   data/pmcs.json - members of pmcs
   data/projects.json - committers of projects
   
   The json files have the format:
   
   dict: key=pmc/project,
         value=dict: key=availid,
         value=array:
         [
         full name,
         time.time() when entry was added to an existing group
         time.time() when entry was last seen,
         ]
    N.B. The timestamps are now saved as an int (the fractional part is not useful)
    However existing entry times have not (yet) been trimmed.
    This would cause a large change to the historical files,
    so to avoid mixing this with a genuine change, it needs to be planned, and
    done between normal updates.
"""
import errtee
import re
from urlutils import UrlCache
import json
import os
import datetime
import time

__HOME = '../data/'

pmcs = {}

print("Reading pmcs.json")
with open(__HOME + "pmcs.json", "r", encoding='utf-8') as f:
    pmcs = json.loads(f.read())

projects = {}
print("Reading projects.json")
with open(__HOME + "projects.json", "r", encoding='utf-8') as f:
    projects = json.loads(f.read())

# Delete mistaken entries
for key in sorted(projects.keys()):
    if key.endswith("-pmc"):
        print("Dropping mistaken entry %s" % key)
        del projects[key]

people = {}
newgroups = []

def updateProjects(stamp, group, cid, cname):
    now = stamp
    if not group in projects:
        print("New unx group %s" % group)
        projects[group] = {}
        newgroups.append(group)
    if not cid in projects[group]: # new to the group
        if group in newgroups: # the group is also new
            now = 0
        print("New unx entry %s %s %s %u" % (group, cid, cname, now))
        projects[group][cid] = [cname, now, stamp]
    else:
        # update the entry last seen time (and the public name, which may have changed)
        projects[group][cid] = [cname, projects[group][cid][1], stamp]

def updatePmcs(stamp, group, cid, cname):
    now = stamp
    project = group[0:-4] # drop the "-pmc" suffix
    if not project in pmcs: # a new project
        print("New pmc group %s" % project)
        pmcs[project] = {}
        newgroups.append(group)
    if not cid in pmcs[project]: # new to the group
        if group in newgroups: # the group is also new
            now = 0
        print("New pmc entry %s %s %s %u" % (project, cid, cname, now))
        pmcs[project][cid] = [cname, now, stamp]
    else:
        # update the entry last seen time (and the public name, which may have changed)
        pmcs[project][cid] = [cname, pmcs[project][cid][1], stamp]
    
print("Reading committer-index.html")
uc = UrlCache()
data = uc.get("http://people.apache.org/committer-index.html","committer-index.html").read().decode('utf-8')

stamp = int(time.time())

print("Scanning committer-index.html")
for committer in re.findall(r"<tr>([\S\s]+?)</tr>", data, re.MULTILINE | re.UNICODE):

##    print(committer)
    """
        <!-- sample with single home URL -->
        <td bgcolor="#a0ddf0"><a id='cwelton'></a>cwelton</td>
        <td bgcolor="#a0ddf0">
        <a href="http://hawq.incubator.apache.org/">Caleb Welton</a></td>        <td bgcolor="#a0ddf0"> <a href='committers-by-project.html#incubator'>incubator</a></td>
        
        <!-- sample with more than one home URL -->
        <td bgcolor="#a0ddf0"><a id='deki'></a>deki</td>
        <td bgcolor="#a0ddf0">
        <a href="https://github.com/deki/">Dennis Kieselhorst</a>|<a href="http://www.dekies.de">+</a></td>
                <td bgcolor="#a0ddf0"> <a href='committers-by-project.html#myfaces'>myfaces</a></td>
        
        <!-- sample with no URL -->
        <td bgcolor="#a0ddf0"><a id='delafran'></a>delafran</td>
        <td bgcolor="#a0ddf0">
        Mark DeLaFranier</td>        <td bgcolor="#a0ddf0"> <a href='committers-by-project.html#geronimo'>geronimo</a></td>
    """
    m = re.search(r"<a id='(.+?)'>[\s\S]+?<td.+?>\s*(.+?)</td>[\s\S]+?>(.+)</td>", committer, re.MULTILINE | re.UNICODE)
    if m:
        cid = m.group(1) # committer id / availid
        cname = re.sub(r"<.+?>", "", m.group(2), 4) # committer name (dropping HTML markup)
        cname = re.sub(r"\|.*", "", cname) # drop additional URL entry names
#         print(cid,cname)
        cproj = m.group(3) # list of authgroups to which the person belongs
        isMember = False
        if re.search(r"<b", committer, re.MULTILINE | re.UNICODE):
            isMember = True
        # process the groups
        for group in re.findall(r"#([-a-z0-9._]+)'", cproj):
            if group.endswith("-pmc"):
                updatePmcs(stamp, group, cid, cname)
            else:
                updateProjects(stamp, group, cid, cname)


# Delete retired members
ret = 0
for project in projects:
    for cid in projects[project]:
        if len(projects[project][cid]) < 3 or projects[project][cid][2] < (time.time() - (86400*3)):
            print("Dropping project entry %s %s" % (project, cid))
            projects[project][cid] = "!" # flag for deletion
            ret += 1
    projects[project] =  {i:projects[project][i] for i in projects[project] if projects[project][i]!="!"}

for project in pmcs:
    for cid in pmcs[project]:
        if len(pmcs[project][cid]) < 3 or pmcs[project][cid][2] < (time.time() - (86400*3)):
            print("Dropping pmc entry %s %s" % (project, cid))
            pmcs[project][cid] = "!" # flag for deletion
            ret += 1
    pmcs[project] =  {i:pmcs[project][i] for i in pmcs[project] if pmcs[project][i]!="!"}


print("Writing pmcs.json")
with open(__HOME + "pmcs.json", "w", encoding='utf-8') as f:
    json.dump(pmcs, f, sort_keys=True, indent=1, ensure_ascii=False)
    f.close()

print("Writing projects.json")
with open(__HOME + "projects.json", "w", encoding='utf-8') as f:
    json.dump(projects, f, sort_keys=True ,indent=1, ensure_ascii=False)
    f.close()

"""
   We want to keep a history of the file because it's not possible
   to recreate the files with all the original joining dates should the
   current files get lost. However the main files contain timestamps that are
   update each time, which would make for unnecessary differences.
   Now only the joining dates are non-recoverable, so we can
   save those separately in the history directory which can then be committed to SVN.
   
   Fix up the dicts to drop the timestamp.
"""
for pmc in pmcs:
    for id in pmcs[pmc]:
        del pmcs[pmc][id][2]

print("Writing history/pmcs.json")
with open(__HOME + "history/pmcs.json", "w", encoding='utf-8') as f:
    json.dump(pmcs, f, sort_keys=True, indent=1, ensure_ascii=False)
    f.close()

for project in projects:
    for id in projects[project]:
        del projects[project][id][2]

print("Writing history/projects.json")
with open(__HOME + "history/projects.json", "w", encoding='utf-8') as f:
    json.dump(projects, f, sort_keys=True ,indent=1, ensure_ascii=False)
    f.close()
    

print("All done! removed %u retired entries" % ret)
