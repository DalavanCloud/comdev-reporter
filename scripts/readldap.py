"""
                          *** DRAFT - NOT READY FOR USE ***
   Read auth groups from LDAP
   
"""

from os.path import getmtime
import json
import time, calendar
import re

import ldap3
from ldap3 import Server, ServerPool, Connection, LEVEL, POOLING_STRATEGY_RANDOM

import urlutils

server1 = Server('ldap1-us-west.apache.org', port=636, use_ssl=True, connect_timeout=5)#, get_info=ALL)
server2 = Server('ldap2-us-west.apache.org', port=636, use_ssl=True, connect_timeout=5)#, get_info=ALL)
server3 = Server('ldap3-us-west.apache.org', port=636, use_ssl=True, connect_timeout=5)#, get_info=ALL)

server_pool = ServerPool([server1, server2, server3], POOLING_STRATEGY_RANDOM, active=True, exhaust=True)

conn = Connection(server_pool, auto_bind=True)

"""
    LDAP filters do not support > or <, so we have to negate <= and >= respectively
    So (a>b) becomes (!(a<=b))
"""

def getPMC(cn, ts=None):
    print('getPMC',cn,ts)
    success = conn.search('ou=committees,ou=groups,dc=apache,dc=org',
                '(&(cn=%s)(!(modifyTimestamp<=%s)))' % (cn, ts) if ts else '(cn=%s)' % cn,
                attributes=['member','createTimestamp','modifyTimestamp','cn'])
    if not success:
        return {}
    members = []
    for c in conn.response:
        att = c['attributes']
        created = att['createTimestamp'][0] # returned as an array of one (!?)
        modified = att['modifyTimestamp'][0]
        for m in att['member']:
            mat = re.search("^uid=(.+),ou=people", m)
            if mat:
                members.append(mat.group(1))
    return {'name': cn,
            'type': 'pmc',
            'roster': sorted(members), # These appear to be listed in order of addition
            'created': created,
            'modified': modified
            }


def getUnix(cn, ts=None):
    success = conn.search('ou=groups,dc=apache,dc=org',
                '(&(cn=%s)(!(modifyTimestamp<=%s)))' % (cn, ts) if ts else '(cn=%s)' % cn,
                attributes=['memberUid','createTimestamp','modifyTimestamp','cn'], search_scope=LEVEL)
    if not success:
        return {}
    members = []
    for c in conn.response:
        att = c['attributes']
        created = att['createTimestamp'][0] # returned as an array of one (!?)
        modified = att['modifyTimestamp'][0]
        members.extend(att['memberUid'])
    return {'name': cn,
            'type': 'unix',
            'roster': sorted(members),
            'created': created,
            'modified': modified
            }

def getLDAPjson(key, unix=True):
    """
        LDAP caching:
    
        Read the json file, if it has a 'modified' entry, then call the getter
        
        To stop excess retries, touch the file and use that as the last checked time?
    """
    if unix:
        filename ='../data/ldapunix/' + key + '.json'
        getter = getUnix
    else:
        filename= '../data/ldappmc/' + key + '.json'
        getter = getPMC
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            old = json.load(f)
            print("Found the file " + filename)
            diff = int(time.time() - getmtime(filename))
            if diff < 300:
                print("Recently checked " + filename + ' ' + str(diff))
                return old
    except FileNotFoundError:
        print("No file found " + filename)
        old = {}
    try:
        modified = old['modified']
    except KeyError:
        print("No modified key")
        modified = None
    new = getter(key, modified)
    print(modified, new)
    if new or modified == None: # we have new data or there was none
        print("Saving " + filename)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(new, f, indent=1, sort_keys=True)        
    else: # old data was OK
        print("Touching "+ filename)
        urlutils.touchFile(filename, time.time())
        new = old
    return new

now=time.time()
d = getLDAPjson('calcite', unix=False)
print(time.time()-now, d)

now=time.time()
d = getLDAPjson('calcite')
print(time.time()-now, d)

die

print(json.dumps(getPMC('calcite','20141027164106Z'), indent=1,sort_keys=True))

print(json.dumps(getUnix('member', '20151022164004Z'), indent=1, sort_keys=True))

# Get the list of PMCs (could use a different source)
with open("../pmcdates.json","r",encoding='utf-8') as f:
    pass
with open("../ldappmc.json","r",encoding='utf-8') as f:
    ldappmc = json.load(f)

with open("../ldapunix.json","r",encoding='utf-8') as f:
    ldapunix = json.load(f)


# print(time.time())
# print(parseTimestamp('20151021002000Z'))
die
for pmc in sorted(pmcdates):
    print("Processing %s" % pmc)
    pmcr = getPMC(pmc)
    print(pmcr)
#     unixr = getUnix(pmc)
    break
# getModified('21151015')
# getPMC('jm*')
# getUnix('jm*')
