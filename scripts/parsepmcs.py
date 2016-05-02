import sys
# The code uses open(..., encoding=enc) which is Python3
if sys.hexversion < 0x030000F0:
    raise RuntimeError("This script requires Python3")
"""
   This script reads: 
   https://whimsy.apache.org/public/committee-info.json
   https://whimsy.apache.org/public/public_ldap_people.json
   https://whimsy.apache.org/public/public_ldap_groups.json
   https://whimsy.apache.org/public/public_ldap_committees.json
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
from urlutils import UrlCache
import json
import time
import re

uc = UrlCache(interval=0)

def loadJson(url):
    print("Reading " + url)
    resp = uc.get(url, name=None, encoding='utf-8', errors=None)
    j = json.load(resp)
    resp.close()
    return j

__HOME = '../data/'

pmcs = {}

print("Reading pmcs.json")
with open(__HOME + "pmcs.json", "r", encoding='utf-8') as f:
    pmcs = json.loads(f.read())

projects = {}
print("Reading projects.json")
with open(__HOME + "projects.json", "r", encoding='utf-8') as f:
    projects = json.loads(f.read())

newgroups = []
newpmcs = []

def updateProjects(stamp, group, cid):
    cname = ldappeople[cid]['name']
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

def updateCommittees(stamp, group, cid):
    cname = ldappeople[cid]['name']
    now = stamp
    if not group in pmcs: # a new project
        print("New pmc group %s" % group)
        pmcs[group] = {}
        newpmcs.append(group)
    if not cid in pmcs[group]: # new to the group
        if group in newpmcs: # the group is also new
            now = 0
        print("New pmc entry %s %s %s %u" % (group, cid, cname, now))
        pmcs[group][cid] = [cname, now, stamp]
    else:
        # update the entry last seen time (and the public name, which may have changed)
        pmcs[group][cid] = [cname, pmcs[group][cid][1], stamp]
    
stamp = int(time.time())

c_info = loadJson('https://whimsy.apache.org/public/committee-info.json')['committees']
ldappeople = loadJson('https://whimsy.apache.org/public/public_ldap_people.json')['people']
ldapgroups = loadJson('https://whimsy.apache.org/public/public_ldap_groups.json')['groups']
ldapcttees = loadJson('https://whimsy.apache.org/public/public_ldap_committees.json')['committees']

for group in ldapcttees:
    if group in c_info:
        for cid in ldapcttees[group]['roster']:
            updateCommittees(stamp, group, cid)
for group in ldapgroups:
    if group != 'committers' and group in c_info:
        for cid in ldapgroups[group]['roster']:
            updateProjects(stamp, group, cid)


"""
   The old code used people.apache.org which included podling groups.
   We don't want these, and we need to remove any existing ones.
   Otherwise we cannot determine when a podling graduates.
   Proactively remove the nonldap groups. 
   [This code can be removed in due course]
"""

nonldapgroups = loadJson('https://whimsy.apache.org/public/public_nonldap_groups.json')['groups']
for nongroup in sorted(nonldapgroups):
    if nongroup not in ldapgroups: # should not happen, but check anyway
        if nongroup in projects:
            print("Dropping non-ldap group %s" % nongroup)
            del projects[nongroup]
#        else:
#            print("Not found non-ldap group %s" % nongroup)
    else:
        print("WARN: unexpected non-ldap group %s in projects list " % nongroup)

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

print("Checking foundation/index.mdtext against list of chairs from committee-info")
chairs={}
for e in c_info:
    if c_info[e]['pmc']:
        v = c_info[e]
        chairs[v['display_name']] = list(v['chair'].values())[0]['name']

chairIndex = 'https://svn.apache.org/repos/asf/infrastructure/site/trunk/content/foundation/index.mdtext'
resp = uc.get(chairIndex, name=None, encoding='utf-8', errors=None)
web={}
for line in resp:
    m = re.match("^\| V.P., \[?Apache (.+?)(\]\(.+?\))? \| (.+?) \|", line)
    if m:
#         print(m.group(1),m.group(3))
        web[m.group(1)] = m.group(3)
chairDiffs = []
for w in web:
    if not w in chairs:
        chairDiffs.append("Missing from cttee %s " % w)
for c in sorted(chairs):
    if not c in web:
        chairDiffs.append("Missing from web page \n| V.P., Apache %s | %s |" % (c, chairs[c]))
    else:
        if not chairs[c] == web[c]:
            chairDiffs.append("Mismatch: Apache %s ctte %s web %s" % (c, chairs[c], web[c]))
        
DEST='Site Development <site-dev@apache.org>'

if len(chairDiffs) == 0:
    print("foundation/index.mdtext list of chairs agrees with committee-info")
else:
    import sendmail
    print("WARN: foundation/index.mdtext list of chairs disagrees with committee-info:")
    for m in chairDiffs:
        print(m)
    try:
        BODY="Comparison of foundation/index.mdtext list of chairs with committee-info\n"
        errs = "\n".join(chairDiffs)
        sendmail.sendMail("foundation/index list of chairs disagrees with committee-info", BODY+"\n"+errs, DEST)
    except Exception as e:
        print("ERROR: unable to send email", e)

print("All done! removed %u retired entries" % ret)
