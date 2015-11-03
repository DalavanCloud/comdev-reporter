import sys
sys.path.append("../../projects.apache.org/scripts") # module committee_info is in p.a.o
import committee_info
import json

"""
Reads committee-info.json via committee_info module

Creates:
../site/reportingcycles.json

"""

cycles = committee_info.cycles()

print("Writing ../site/reportingcycles.json")
with open("../site/reportingcycles.json", "w", encoding='utf-8') as f:
    json.dump(cycles, f, sort_keys = True, indent=1, ensure_ascii=False)
    f.close()

print("All done!")