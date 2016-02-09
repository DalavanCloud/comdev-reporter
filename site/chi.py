#!/usr/bin/env python
import os, re, json
import cgi
from os.path import join

RAO_DATA = '/var/www/reporter.apache.org/data'

user = os.environ['HTTP_X_AUTHENTICATED_USER'] if 'HTTP_X_AUTHENTICATED_USER' in os.environ else ""
m = re.match(r"^([-a-zA-Z0-9_.]+)$", user)

if m:
    with open(join(RAO_DATA,"health.json"), "r") as f:
        notes = json.load(f)
        f.close()
        
    status = [0,0,0,0,0,0]
    print ("Content-Type: text/html\r\n\r\n<h1><img src='/img/chi.png' style='vertical-align: middle;'/> Community Health Issues</h1><p>This is a quantitative guideline only. There may be niche cases where the summaries below to not apply. <br/>Scores range from -10.00 (worst possible score) to +10.00 (best possible score), harmonized by <img src='/img/equation.png' style='vertical-align: middle;'/></p>")
    values = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
    xvalues = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
    colors = ["#000070", "#007000", "#407000", "#70500", "#700000", "#A00000"]
    for entry in sorted(notes, key=lambda x: x['score'], reverse=True):
        s = int(entry['score']/1.80)
        if s > 4:
            s = 4
        s = s + 1
        if s < 0:
            s = 0
        status[s] += 1;
    
    y = 0
    for s in status:
        xvalues[y] = "%s (%u)" % (values[y], s)
        y += 1
    print('<img src="https://chart.googleapis.com/chart?cht=p&amp;chs=640x260&amp;chd=t:%s&amp;chl=%s&amp;chco=0000A0|00A000|A0D000|F0D000|F08500|A00000"/><br/><br/>' % ( ",".join(str(x) for x in status), "|".join(xvalues)))
          
    for entry in sorted(sorted(notes, key=lambda x: x['group']), key=lambda x: x['score'], reverse=True):
        s = int(entry['score']/1.80)
        if s > 4:
            s = 4
        s = s + 1
        if s < 0:
            s = 0
        status[s] += 1;
        print("<font color='%s'>\r" % colors[s])
        print( "<b id='%s'>%s%s: %s%s</b><br/>\r" % (entry['group'], "<u>" if s >= 4 else "", entry['pmc'], values[s],"</u>" if s >= 4 else "",  ))
        print( "<blockquote><b>Health score:</b> %0.2f<br>\r" % (6.33+((-1 * entry['score'])* (20/12.25))))
        for l in entry['notes']:
            print("<b>Score note: </b>%s<br/>\r" % l)
        print("</blockquote></font><hr/>\r")
else:
    print ("Content-Type: text/html\r\n\r\n")
    print("Unknown or invalid user id presented")
