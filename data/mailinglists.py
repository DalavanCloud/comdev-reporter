import sys
if sys.hexversion < 0x030000F0:
    raise RuntimeError("This script requires Python3")
"""
   This script creates mailinglists.json
"""
import json
import urllib.request
import os

mailurl = ""
with open("%s/.mailurl" % os.environ['HOME'], "r") as f:
    mailurl = f.read().strip()
    f.close()

print("Reading mail subscription details")

data = urllib.request.urlopen(mailurl).read().decode('utf-8')
maildata = json.loads(data, encoding='utf-8')

print("Writing mailinglists.json")
with open("mailinglists.json", "w", encoding='utf-8') as f:
    json.dump(maildata, f, sort_keys=True, indent=1, ensure_ascii=False)
    f.close()
