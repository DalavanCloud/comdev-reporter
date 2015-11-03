import sys
sys.path.append("../../projects.apache.org/scripts") # module committee_info is in p.a.o
import committee_info
import json
import time

"""

Parse PMC start dates and member joining dates

Reads committee-info.json via committee_info module

Creates:
pmcdates.json
Format:
{ 
  "pmc1": {
     "pmc": [ 'start date (MM/YYYY)', pmc startdate(secs since epoch), earliest committer startdate(secs since epoch) ]
     "roster": {
        "id1": [ "Full name", start date (secs since epoch) ]
     }
  },
}

Note that the earliest startdate is set to 0 if there is no entry with the same month and year as the text start date.
Thus if it *is* present, it is almost certainly the actual start date of the PMC.
If it is not present, either there are no remaining members of the original PMC (spamassassin/maven),
or the PMC was restarted (apr, xalan)
(or it's just possible that committee-info may be wrong)

"""

__PMCDATES = "../data/pmcdates.json"

pmcdates = committee_info.pmcdates()

for pmc in sorted(pmcdates):
    roster = pmcdates[pmc]['roster']
    startdate = pmcdates[pmc]['pmc'][0]
    earliest = 0 # no date found
    for id in roster:
        joindate = roster[id][1]
        if earliest == 0 or joindate < earliest:
            earliest = joindate
    earliestMMYYYY = time.strftime('%m/%Y',time.gmtime(earliest))
    if earliestMMYYYY == startdate:
        pmcdates[pmc]['pmc'].insert(2, earliest)
    else:
        pmcdates[pmc]['pmc'].insert(2, 0)
        print(time.strftime('%Y-%m-%d = %m/%Y',time.gmtime(earliest)),startdate, pmc)
    
print("Writing " + __PMCDATES)
with open(__PMCDATES, "w", encoding='utf-8') as f:
    json.dump(pmcdates, f, sort_keys = True, indent=1, ensure_ascii=False)

print("All done!")