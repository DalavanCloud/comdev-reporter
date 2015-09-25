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


mls = {}
try:
    with open("data/maildata_extended.json",'r') as f:
        mls = json.loads(f.read())
    print("Read JSON")
except:
    pass

currentMonth = datetime.now().month
currentYear = datetime.now().year
after = time.time() - (SECS_PER_DAY*92)
wayafter = time.time() - (SECS_PER_DAY*92*2)
months = []
for i in range(0,7):
    date = "%04u%02u" % (currentYear, currentMonth)
    currentMonth -= 1
    if currentMonth == 0:
        currentMonth = 12
        currentYear -= 1
    months.append(date)

    now = int(time.time())

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
for mlist in re.finditer(r"<a href='([-a-z0-9]+)/'", data):
    ml = mlist.group(1)
    y += 1
    mls[ml] = {}
    mls[ml]['quarterly'] = [0, 0];
    mls[ml]['weekly'] = {}
    for date in months:
            
        try:
            mldata = urllib.urlopen("http://mail-archives.us.apache.org/mod_mbox/%s/%s.mbox" % (ml, date)).read()
            if mldata:
                for c in re.finditer(r"Date: (.+)", mldata):
                    try:
                        d = email.utils.parsedate(c.group(1))
                        timestamp = int(time.mktime(d))
                        rounded = timestamp - (timestamp % 604800) + 604800
                        mls[ml]['weekly'][rounded] = (mls[ml]['weekly'][rounded] if rounded in mls[ml]['weekly'] else 0) + 1
                        if timestamp >= after:
                            mls[ml]['quarterly'][0] += 1
                        elif timestamp >= wayafter:
                            mls[ml]['quarterly'][1] += 1
                    except:
                        pass
                        
        except Exception as err:
            print(err)
    print("%s: %u" % (ml, mls[ml]['quarterly'][0]))
    if y == 50:
        y = 0
        with open("data/maildata_extended.json",'w+') as f:
            f.write(json.dumps(mls, indent=1))
with open("data/maildata_extended.json",'w+') as f:
    f.write(json.dumps(mls, indent=1))
print("Dumped JSON")
