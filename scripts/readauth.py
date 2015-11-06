"""
   Read non-LDAP auth groups from the deployed Git copies of:
   - asf-authorization-template
   - pit-authorization-template
   
   Output:
   - data/authByGroup.json - list of groups and their members
   - data/authByUser.json - list of users and their groups
"""

from urlutils import UrlCache
import re
import json

DATA_HOME = '../data/'
AUTH_BY_GROUP = DATA_HOME + 'authByGroup.json'
AUTH_BY_USER  = DATA_HOME + 'authByUser.json'

GIT='https://git-wip-us.apache.org/repos/asf?p=infrastructure-puppet.git;hb=refs/heads/deployment;a=blob_plain;f=modules/subversion_server/files/authorization/'
ASF='asf-authorization-template'
PIT='pit-authorization-template'

uc=UrlCache()

authByGroup = {}
authByUser = {}

def _process(name, addUser=True, addGroup=True):
    print("Processing %s" % name)
    with uc.get(GIT+name, name, encoding='utf-8') as f:
        for line in f:
            if re.match(r"^\[/\]", line):# end of definition section
                return
            m = re.match(r"^\s*(\w\S+?)\s*=\s*(\S+)$", line)
            if m:
                entry = m.group(1)
                value = m.group(2)
                if entry in authByGroup:
                    if not value.startswith("{reuse:"):
                        print("ERROR: %s contains duplicate group %s" % (name, line))
                else:
                    if not value[0:1] == '{':
                        roster = value.split(',')
                        if addGroup:
                            authByGroup[entry] = {
                                             'name': name,
                                             'roster': roster
                                             }
                        if addUser:
                            for user in roster:
                                if not user in authByUser:
                                    authByUser[user] = []
                                authByUser[user].append(entry)

def getAuthByUser():
    """
       Return the users and their groups as defined in asf-authorization-template
       Does not return groups defined in LDAP
    """
    _process(ASF)
    return authByUser

if __name__ == '__main__':
    print("Start")

    print("Reading " + ASF)
    _process(ASF)
    
    print("Reading " + PIT)
    _process(PIT, addUser=False) # we don't want to expose these at present
    
    print("Writing " + AUTH_BY_GROUP)
    with open(AUTH_BY_GROUP,'w') as f:
        json.dump(authByGroup, f, indent=1, sort_keys=True)
    
    print("Writing " + AUTH_BY_USER)
    with open(AUTH_BY_USER,'w') as f:
        json.dump(authByUser, f, indent=1, sort_keys=True)

    print("All done")

    