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


uc = UrlCache(interval=0, silent=True)

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

def cycles():

    committees = cidata['committees']

    cycles={}
    for ctte in committees:
        c = committees[ctte]
        if not c['pmc']:
            continue
        cycles[ctte] = c['report']
        # Duplicate some entries for now so the code can find them (the existing json has the duplicates)
        if ctte == 'ws': # Special processing
            cycles['webservices'] = cycles[ctte]
        if ctte == 'httpd': # Special processing
            cycles['http server'] = cycles[ctte]
    return cycles

"""
Returns an array of entries of the form:

    "abdera": {
      "fullname": "Apache Abdera",
      "mail_list": "abdera",
      "established": "2008-11",
      "report": [
        "February",
        "May",
        "August",
        "November"
      ],
       "reporting": 2,
      "chair": {
        "nick": "antelder",
        "name": "Ant Elder"
        },
      "pmc": true
      },

"""
def committees():

    committees = {}
    cttes = cidata['committees']
    for ent in cttes:
        ctte = cttes[ent]
        c = {}
        for key in ctte:
            # some keys need special processing
            if key == 'display_name':
                basename = ctte['display_name']
                c['fullname'] = "Apache %s" % ('mod_perl' if basename == 'Perl' else basename)
            elif key == 'chair':
                c['chair'] = None
                for ch in ctte['chair']:
                    c['chair'] = {
                    'nick': ch,
                    'name': ctte['chair'][ch]['name']}
            elif key == 'established':
                value = ctte[key]
                if value:
                    value = "%s-%s" % (value[3:7], value[0:2]) # extract year and month
                c[key] = value
            elif key == 'report':
                c[key] = ctte[key] # save original values
                value = ctte[key]
                if 'January' in value:
                    c['reporting'] = 1
                elif 'February' in value:
                    c['reporting'] = 2
                elif 'March' in value:
                    c['reporting'] = 3
                elif 'Every month' in value:
                    c['reporting'] = 0
            else:
                c[key] = ctte[key]
        committees[ent]=c
    return committees

def pmcdates():
    dates = {}
    
    cttes = cidata['committees']
    for ent in cttes:
        ctte = cttes[ent]
        if not ctte['pmc']:
            continue
        roster = ctte['roster']
        est = ctte['established']
        date = 0
        if not est == None:
            # convert mm/yyyy to date (drop any subsequent text)
            try:
                date = calendar.timegm(time.strptime(est[0:7], '%m/%Y'))
            except Exception as e:
                print("Date parse error for %s: %s %s" % (ent, est, e))
                pass
        dates[ent] = {'pmc': [est, date], 'roster': {} }
        ids = {}
        for id in roster:
            rid = roster[id]
            try:
                date = calendar.timegm(time.strptime(rid['date'], '%Y-%m-%d'))
            except:
                date = 0
            ids[id] = [rid['name'], date]
        dates[ent]['roster'] = ids
        # The 'CI' internal name for Web Services is 'ws' but reporter code originally used 'webservices'
        if ent == 'ws':
            dates['webservices'] = dates[ent]
    return dates

if __name__ == '__main__':
    import sys
    json.dump(PMCnames(), sys.stdout, indent=1, sort_keys=True)
    json.dump(cycles(), sys.stdout, indent=1, sort_keys=True)
    json.dump(pmcdates(), sys.stdout, indent=1, sort_keys=True)
    json.dump(committees(), sys.stdout, indent=1, sort_keys=True)
