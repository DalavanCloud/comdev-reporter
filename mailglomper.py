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
import re, json, os, sys, urllib, time, email.utils

from datetime import datetime

SECS_PER_DAY = 86400
SECS_PER_WEEK = 604800


mls = {}
try:
    with open("data/maildata_extended.json",'r') as f:
        mls = json.loads(f.read())
    print("Read JSON")
except:
    pass


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

data = urllib.urlopen("http://mail-archives.us.apache.org/mod_mbox/").read()
print("Fetched %u bytes of main data" % len(data))
y = 0
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

def tsprint(s): # print with timestamp
    print("%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), s))

tsprint("Started")

for mlist in re.finditer(r"<a href='([-a-z0-9]+)/'", data):
    ml = mlist.group(1)
    start = time.time()
#     print(ml)
    y += 1
    mls[ml] = {}
    mls[ml]['quarterly'] = [0, 0];
    mls[ml]['weekly'] = {}
    mlct = 0
    for date in months:            
        try:
            ct = 0
            mldata = urllib.urlopen("http://mail-archives.us.apache.org/mod_mbox/%s/%s.mbox" % (ml, date))
            for line in mldata:
                c = re.match(r"^From \S+ (.+)", line)
                if c:
                    ct += 1
                    try:
                        d = email.utils.parsedate(c.group(1))
                        timestamp = int(time.mktime(d))
                        rounded = timestamp - (timestamp % SECS_PER_WEEK) + SECS_PER_WEEK
                        mls[ml]['weekly'][rounded] = (mls[ml]['weekly'][rounded] if rounded in mls[ml]['weekly'] else 0) + 1
                        if timestamp >= after:
                            mls[ml]['quarterly'][0] += 1
                        elif timestamp >= wayafter:
                            mls[ml]['quarterly'][1] += 1
                    except Exception as err:
                        tsprint(err)
                        pass
#             tsprint("%s %s: has  %u mails" % (ml, date, ct)) # total for month
            mlct += ct
        except Exception as err:
            tsprint(err)
    tsprint("Info: %s has  %u mails (%u secs)" % (ml, mlct, time.time() - start)) # total for mail group
    if y == 50:
        y = 0
        with open("data/maildata_extended.json",'w+') as f:
            json.dump(mls, f, indent=1)
tsprint("Completed scanning, writing JSON")
with open("data/maildata_extended.json",'w+') as f:
    json.dump(mls, f, indent=1)
print("Dumped JSON")
