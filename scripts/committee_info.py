"""

Module to give access to data from committee-info.json

This module acts as the gatekeeper for all access to committee-info.json
which is cached from https://whimsy.apache.org/public/committee-info.json

"""

import time
import calendar
import json
from urlutils import UrlCache

URL='https://whimsy.apache.org/public/committee-info.json'


# Don't check more often than every minute (used by webapp as well as cronjobs)
uc = UrlCache(interval=60, silent=True)

def loadJson(url):
    resp = uc.get(url, name=None, encoding='utf-8', errors=None)
    try:
        content = resp.read() # json.load() does this anyway
        try:
            j = json.loads(content)
        except Exception as e:
            # The Proxy error response is around 4800 bytes
            print("Error parsing response:\n%s" % content[0:4800])
            raise e
    finally:
        resp.close()
    return j

cidata = {} # The data read from the file


def update_cache():
    global cidata # Python defaults to creating a local variable
    cidata = loadJson(URL)

update_cache() # done when loading

def PMCnames():

    """
        Returns output of the form:
        {
         "ace": "Apache ACE",
         "abdera": "Apache Abdera,
         ...
        }
        Only includes actual PMC names
        Returns 'webservices' rather than 'ws'
    """
    committees = cidata['committees']

    namejson={}
    for ctte in committees:
        c = committees[ctte]
        if not c['pmc']:
            continue
        name = 'Apache %s' % c['display_name']
        if ctte == 'ws': ctte = 'webservices'
        namejson[ctte] = name

    return namejson

def PMCsummary():

    """
        Returns output of the form:
        {
         "ace": {
           "name": "Apache ACE",
           "chair": "Chair 1",
           "report": [
             "February",
             "May",
             "August",
             "November"
             ]
           },
         "abdera": {
           "name": "Apache Abdera",
           "chair": "Chair 2",
           "report: [...]
           },
         ...
        }
        Only includes actual PMCs
        Returns 'webservices' rather than 'ws'
    """
    committees = cidata['committees']

    namejson={}
    for ctte in committees:
        c = committees[ctte]
        if not c['pmc']:
            continue
        name = 'Apache %s' % c['display_name']
        if ctte == 'ws': ctte = 'webservices'
        chair = 'Unknown'
        chs = c['chair']
        for ch in chs: # allow for multiple chairs
            chair = chs[ch]['name']
            break
        namejson[ctte] = {
                      'name': name,
                      'report': c['report'],
                      'chair': chair
                      }

    return namejson


if __name__ == '__main__':
    import sys
    json.dump(PMCnames(), sys.stdout, indent=1, sort_keys=True)
    json.dump(PMCsummary(), sys.stdout, indent=1, sort_keys=True)
