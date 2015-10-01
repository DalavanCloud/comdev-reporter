import sys
sys.path.append("../../projects.apache.org/scripts") # module committee_info is in p.a.o
import committee_info
import json

"""

Parse PMC start dates and member joining dates

Reads committee-info.json via committee_info module

Creates:
pmcdates.json

"""

pmcdates = committee_info.pmcdates()

print("Writing pmcdates.json")
with open("pmcdates.json", "w", encoding='utf-8') as f:
    json.dump(pmcdates, f, sort_keys = True, indent=1, ensure_ascii=False)
    f.close()

print("All done!")