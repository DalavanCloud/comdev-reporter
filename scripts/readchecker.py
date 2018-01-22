#!/usr/bin/env python3

"""
   Refreshes the data/cache/checker.json file

   This script is run under cron, so does not check the age of any files.
   It is assumed that the job is run as frequently as necessary
   to keep the files updated
"""

import errtee
import re, os, json, base64, time
try:
    from urllib.request import urlopen, Request
    py3 = True
except:
    from urllib2 import urlopen,Request
    py3 = False
from os import listdir
from os.path import isfile, join, dirname, abspath
from inspect import getsourcefile

MYHOME = dirname(dirname(abspath(getsourcefile(lambda:0)))) # automatically work out home location so can run the code anywhere
SRC = "https://checker.apache.org/json/"
DST = "%s/cache/checker.json" % MYHOME
print("Using MYHOME=%s" % MYHOME)
print("Using source [%s]" % SRC)
print("Using dest   [%s]" % DST)

TIMEOUT = 90 # This may need to be adjusted
load_errors = 0 # count how many errors occurred
def handleError():
    global load_errors
    load_errors += 1
    if load_errors > 5:
        raise Exception("Too many errors - quitting")

def getJson(src,dst):
    print("Refresh %s ..." % dst)
    try:
        req = Request(src)
        x = json.loads(urlopen(req, timeout=TIMEOUT).read().decode('utf-8'))
        tmp = "%s.tmp" % dst
        old = "%s.old" % dst
        with open(tmp, "w") as f:
            json.dump(x, f, indent=1, sort_keys=True)
            f.close()
            print("Created %s" % tmp)
            if os.path.isfile(dst):
                os.rename(dst,old)
            os.rename(tmp,dst)
            print("Renamed %s" % dst)
    except Exception as e:
        print("Err: could not refresh %s: %s" % (dst, e))
        handleError()

getJson(SRC,DST)

print("Done")
