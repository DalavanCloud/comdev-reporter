# Parse committee-info.json to generate reportingcycles.json
# TODO not yet ready for use

import json
import re

input={}
ci = "data/committee-info.json" # TODO may be URL

output={}
out="site/reportingcycles2.json" # TODO temp file name

print("Reading %s" % ci)
with open(ci, "r") as inp:
    input = json.loads(inp.read())
    inp.close()

# extract just the data we need
committees=input['committees']
for project in sorted(committees):
    pdata = committees[project]
    if not pdata['pmc']: # "pmc:" false
        print("%s - skipped, not a PMC" % project)
        continue
    print(project)
    output[project]=[]
    report = pdata['report']
    # TODO may need to change this; report entry may be changed to array
    # Next month may include comma-space
    if re.match('^Next month:', report):
            output[project].append(report)
    else:
        report=re.split(',\s*', pdata['report'])
        for period in report:
            output[project].append(period)

print("Writing %s" % out)
with open(out, "w") as out:
    out.write(json.dumps(output, indent=1, sort_keys=True))
    out.close()
