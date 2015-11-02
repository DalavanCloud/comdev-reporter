"""
   Reads public mailing list data from
   http://mail-archives.us.apache.org/mod_mbox/
   - listing of mailboxes
   and from each:
   http://mail-archives.us.apache.org/mod_mbox/<list>/yyyymm.mbox
   - messages per week and per last two rolling quarters (92 days)
   
   Updates:
   data/maildata_extended.json
"""
import sys
if sys.hexversion < 0x03000000:
    raise ImportError("This script requires Python 3")
import re, json, os, time, email.utils, signal
from datetime import datetime
import urlutils
import urllib.error
import traceback
import data.errtee

SECS_PER_DAY = 86400
SECS_PER_WEEK = 604800

def tsprint(s): # print with timestamp
    msg = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), s)
    if isinstance(s, Exception):
        print(msg, file=sys.stderr)
        type, value, tb = sys.exc_info()
        traceback.print_exception(type, value, tb)
    else:
        print(msg)

interrupted = False

def handle(signum, frame):
    global interrupted # otherwise handler does not set the same variable
    interrupted = True
    tsprint("Interrupted with %d" % signum)

tsprint("Start")

__MAILDATA_EXTENDED = "data/maildata_extended2.json" # TODO change to normal name

__MAILDATA_CACHE    = "data/cache/maildata_weekly.json"

try:
    with open(__MAILDATA_EXTENDED,'r') as f:
        mls = json.loads(f.read())
    tsprint("Read JSON successfully")
except:
    mls = {}

try:
    with open(__MAILDATA_CACHE,'r') as f:
        mldcache = json.loads(f.read())
    tsprint("Read maildata cache successfully")
except:
    tsprint("Created empty maildata cache")
    mldcache = {}

DTNOW = datetime.now()
currentMonth = DTNOW.month
currentYear = DTNOW.year

NOW = time.time()
after = NOW - (SECS_PER_DAY*92)
wayafter = NOW - (SECS_PER_DAY*92*2)

months = []
for i in range(0,7):
    date = "%04u%02u" % (currentYear, currentMonth)
    currentMonth -= 1
    if currentMonth == 0:
        currentMonth = 12
        currentYear -= 1
    months.append(date)

# Remove any stale entries
obsolete = [] # list of keys to remove (cannot do it while iterating)
for mld in mldcache.keys():
    yyyymm = mld[-6:]
    if yyyymm not in months:
        obsolete.append(mld)

for key in obsolete:
    tsprint("Dropping obsolete cache entry: " + key)
    del mldcache[key]

fc = urlutils.UrlCache(interval=30)

# Get the index of mailing lists
# Not strictly necessary to cache this, but it makes testing easier
data = fc.get("http://mail-archives.us.apache.org/mod_mbox/", "mod_mbox.html", encoding='utf-8').read()
tsprint("Fetched %u bytes of main data" % len(data))

"""
N.B. The project name empire-db is truncated to empire in the main list

Rather than fixing this here, it is done in the scripts that read the output file
This is because those scripts assume that the first hyphen separates the
project name from the mailing list name.
Since list names may contain hyphens (e.g. lucene-net-dev) that is a necessary assumption.

Potentially the generated file could use a separator that is not allowed in project names,
but this would require converting the input file and potentially allowing both separators in
the files that process the output for a short while.
"""

def weekly_stats(ml, date):
    """
       Read the weekly stats from a mbox file, caching the counts.
    """
    fname = "%s-%s" % (ml, date)
    stampold = None
    if fname in mldcache:
#         tsprint("Have json cache for: " + fname)
        entry = mldcache[fname]
        ct = entry['ct']
        stampold = entry['stamp']
        weekly = {}
        # JSON keys are always stored as strings; fix these up for main code
        for w in entry['weekly']:
            weekly[int(w)] = entry['weekly'][w]
    else:
#         tsprint("Not cached: " + fname)
        pass

    url = "http://mail-archives.us.apache.org/mod_mbox/%s/%s.mbox" % (ml, date)
    stamp, mldata = urlutils.getIfNewer(url, stampold) # read binary URL

    if mldata: # we have a new/updated file to process
        tsprint("Processing new/updated version of %s (%s > %s)" % (fname, stamp, stampold))
        ct = 0
        weekly = {}
        l = 0
        for line in mldata:
            l += 1
            c = re.match(b"^From \S+ (.+)", line) # match as binary
            if c:
                ct += 1
                try:
                    d = email.utils.parsedate(c.group(1).decode('latin1')) # convert match to string
                    timestamp = int(time.mktime(d))
                    rounded = timestamp - (timestamp % SECS_PER_WEEK) + SECS_PER_WEEK
                    weekly[rounded] = (weekly[rounded] if rounded in weekly else 0) + 1
                except Exception as err:
                    tsprint(err)
        # create the cache entry        
        mldcache[fname] = {
                              'ct': ct,
                              'weekly': weekly,
                              'stamp': stamp
                            }
    else:
#         tsprint("Returning cache for: " + fname)
        pass
    # return the new or cached values
    return ct, weekly

def add_weeks(total, add):
    for e in add:
        if e in total:
            total[e] += add[e]
        else:
            total[e] = add[e]

tsprint("Started")
signal.signal(signal.SIGINT, handle)
signal.signal(signal.SIGTERM, handle)

lastCheckpoint = time.time() # when output files were last saved
for mlist in re.finditer(r"<a href='([-a-z0-9]+)/'", data):
    ml = mlist.group(1)
    tsprint("Processing: " + ml)
    start = time.time()
    mls[ml] = {}
    mls[ml]['quarterly'] = [0, 0];
    mls[ml]['weekly'] = {}

    mlct = 0
    for date in months:
        try:
            ct, weeks = weekly_stats(ml, date)
            add_weeks(mls[ml]['weekly'], weeks)
            for week in weeks:
                if week >= after:
                    mls[ml]['quarterly'][0] += weeks[week]
                elif week >= wayafter:
                    mls[ml]['quarterly'][1] += weeks[week]
            tsprint("Debug: %s %s: has %u mails" % (ml, date, ct)) # total for month
            mlct += ct
        except urllib.error.HTTPError as err:
            if err.code == 404:
                tsprint("Warn: could not open %s-%s - %s" % (ml, date, err.reason))
            else:
                tsprint(err)
        except Exception as err:
            tsprint(err)
        if interrupted:
            break

    tsprint("Info: %s has %u mails (%u secs)" % (ml, mlct, time.time() - start)) # total for mail group
    now = time.time()
    if now - lastCheckpoint > 600: # checkpoint every 10 minutes
        lastCheckpoint = now
        tsprint("Creating checkpoint of JSON files")
        with open(__MAILDATA_EXTENDED,'w+') as f:
            json.dump(mls, f, indent=1) # sort_keys is expensive
        with open(__MAILDATA_CACHE,"w") as f:
            json.dump(mldcache, f, indent=1) # sort_keys is expensive

    if interrupted:
        break

tsprint("Completed scanning, writing JSON files (%s)" % str(interrupted))
with open(__MAILDATA_EXTENDED,'w+') as f:
    json.dump(mls, f, indent=1, sort_keys=True)
with open(__MAILDATA_CACHE,"w") as f:
    json.dump(mldcache, f, indent=1, sort_keys=True)
tsprint("Dumped JSON files")
