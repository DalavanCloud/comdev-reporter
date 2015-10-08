import sys
# The code uses urllib.request which is Python3
if sys.hexversion < 0x030000F0:
    raise RuntimeError("This script requires Python3")
"""
   This script runs a couple of Bugzilla reports:
   - all bugs that were created in the last 3 months  
   - all RESOLVED bugs that changed to RESOLVED in the last 3 months
   and creates an output file:
   { "pmc1" : [created, resolved],
     "pmc2: ...
   }
   
"""
import re
import urllib.request
import json

BASE = "https://bz.apache.org/bugzilla/report.cgi?y_axis_field=product&ctype=csv&format=table&action=wrap"
CREATED = "&f1=creation_ts&o1=greaterthaneq&v1=-3m"
RESOLVED = "&chfield=bug_status&chfieldvalue=RESOLVED&chfieldfrom=-3m&chfieldto=Now"

def getCSV(url):
    csv = {}
    with urllib.request.urlopen(url) as f:
        lines = f.read().decode('utf-8').splitlines()
        for l in lines[1:]: # Drop header
            product, count = l.split(',')
            # product is enclosed in quotes; drop them
            csv[product[1:-1]] = int(count)
        f.close()
    return csv

# test data:
# created = {'JMeter': 57, 'Ant': 15, 'APR': 10, 'Log4j': 3, 'WebSH': 1, 'Tomcat 9': 4, 'Apache httpd-2': 64, 
#          'Tomcat 7': 25, 'Tomcat Connectors': 8, 'Tomcat 6': 4, 'Taglibs': 1, 'Tomcat Native': 6, 'Tomcat 8': 85, 'POI': 90}
# resolved = {'JMeter': 33, 'Ant': 8, 'APR': 2, 'Log4j': 2, 'WebSH': 1, 'Tomcat 9': 3, 'Apache httpd-2': 35, 
#           'Tomcat 7': 26, 'Tomcat Modules': 1, 'Tomcat Connectors': 7, 'Tomcat 6': 5, 'Taglibs': 2, 'Tomcat Native': 1, 'Tomcat 8': 88, 'POI': 115, 'Rivet': 0}

print("Getting list of bugs created in the last 3 months")
created = getCSV(BASE+CREATED)
 
print("Getting list of bugs resolved in the last 3 months")
resolved = getCSV(BASE+RESOLVED)

stats = {}

# Other bugzilla users are Ant, APR, JMeter, POI
prod2pmc = {
    'log4j': 'logging',
    'websh': 'tcl',
    'rivet': 'tcl',
    'taglibs': 'tomcat',
    }

def getPMC(product):
    if product.startswith("Tomcat "):
        return 'tomcat'
    if product.startswith('Apache httpd'):
        return 'httpd'
    low = product.lower()
    if low in prod2pmc:
        return prod2pmc[low]
    return low

def addCount(product, index, count):
    pmc = getPMC(product)
    if not pmc in stats:
        stats[pmc]=[0,0,{}]
    stats[pmc][index] += count
    try:
        stats[pmc][2][product][index] += count
    except KeyError:
        stats[pmc][2][product] = [0,0]
        stats[pmc][2][product][index] = count

for product in created:
    addCount(product, 0, created[product])

for product in resolved:
    addCount(product, 1, resolved[product])
print("Writing bugzillastats.json")
with open("bugzillastats.json","w") as f:
    json.dump(stats, f, indent=1, sort_keys=True)
    f.close()
print("All done")