This file is an attempt to start to document how the reporter.apache.org site is set up.

It is currently very rudimentary.



Javascript and CSS are Foundation
http://foundation.zurb.com
Current version seems to be 5.5.1 (see start of site/css/foundation.css)

Also uses Google Loader:
https://developers.google.com/loader/
This is used by site/index.html which loads the visualization API modules: corechart, timeline

The site seems to run on the host nyx-ssl

The HTTPD conf is defined here:
https://svn.apache.org/repos/infra/infrastructure/trunk/machines/vms/nyx-ssl.apache.org/etc/apache2/sites-available/reporter.apache.org.conf

Some Puppet data is here
https://svn.apache.org/repos/infra/infrastructure/trunk/puppet/hosts/nyx-ssl/manifests/init.pp

The apache puppet config for the VM is stored at:
https://git-wip-us.apache.org/repos/asf?p=infrastructure-puppet.git;a=blob_plain;f=data/nodes/projects-vm.apache.org.yaml

There must be other puppet data files for the host; details TBA

Crontab:

crontab -l -u root (in puppet, part of projects-vm.apache.org.yaml):
# m h  dom mon dow   command

10 4,12,20   * * * cd /var/www/reporter.apache.org/data/history  && svn ci -m "updating reporter data" --username projects_role --password `cat /root/.rolepwd` --non-interactive
45 0,6,12,18 * * * cd /var/www/reporter.apache.org/data/releases && svn ci -m "updating reporter data" --username projects_role --password `cat /root/.rolepwd` --non-interactive

crontab -l -u www-data:
# m h   dom mon dow   command
00 4,12,20 * * * cd /var/www/reporter.apache.org/data && ./python3logger.sh parsepmcs.py
10 00      * * * cd /var/www/reporter.apache.org/data && ./python3logger.sh reportingcycles.py
20 00      * * * cd /var/www/reporter.apache.org/data && ./python3logger.sh pmcdates.py
30 00      * * * cd /var/www/reporter.apache.org/data && ./python3logger.sh bugzillastats.py

# ensure that any new data files get picked up by the commit (which must be done by root)
# TODO: either discard the output or work out how to log it (with timestamps) if there is any output
40 * * * *      cd /var/www/reporter.apache.org/data/releases && ( svn status | awk '/^\? / {print $2}' | xargs -r svn add )

00 01      * * * cd /var/www/reporter.apache.org/ && ./pythonlogger.sh mailglomper.py
00 09      * * * cd /var/www/reporter.apache.org/ && ./pythonlogger.sh readjira.py

00 12      * * * curl -sS "(redacted)" > /var/www/reporter.apache.org/data/mailinglists.json

# Run pubsubber
@reboot         cd /var/www/projects.apache.org/scripts/cronjobs && ./pubsubber.sh

# Run scandist
@reboot         cd /var/www/reporter.apache.org && ./restart_scandisk.sh

Scripts:
- data/parsepmcs.py
  Updates data/pmcs.json and data/projects.json (currently from http://people.apache.org/committer-index.html)
  Also updates historic copies (without the last seen timestamp) in data/history

-data/pmcdates.py
  Creates data/pmcdates.json from committee_info.json

-data/reportingcycles.py
  Creates site/reportingcycles.json from committee_info.json

- mailglomper.py
  Updates data/maildata_extended.json from http://mail-archives.us.apache.org/mod_mbox/<list>/<date>.mbox

- readjira.py
  Creates JSON files under data/JIRA

- addrelease.py
  Updates data/releases/%s.json % committee from form data

- site/chi.py
  Creates data/health.json

- site/getjson.py
  If stale, re-creates data/JIRA/projects.json (from JIRA)
  If stale, re-creates data/JIRA/%s.json % project (from JIRA)
  
- site/jiraversions.py
  Updates data/releases/%s.json % project

- parseversions.py - is this used anywhere?
  Updates data/releases/%s.json project from JIRA

Data file consumers:
Note: the prefix ~pao means that the file is held under the projects.apache.org workspace
- chi.py
  data/maildata_extended.json
  data/mailinglists.json
  data/pmcs.json
  data/projects.json
  data/releases/%s.json % project
  ~pao/site/json/foundation/pmcs.json
  ~pao/site/json/foundation/chairs.json
  ~pao/site/json/projects/%s.json % project

- deathnote.py
  data/maildata_extended.json
  data/mailinglists.json
  data/pmcs.json
  data/projects.json
  data/releases/%s.json % project
  ~pao/site/json/foundation/pmcs.json
  ~pao/site/json/foundation/chairs.json
  ~pao/site/json/projects/%s.json % project

- getjson.py
  data/health.json
  data/maildata_extended.json
  data/mailinglists.json
  data/pmcs.json
  data/projects.json
  data/pmcdates.json
  data/releases/%s.json % project
  data/JIRA/projects.json
  data/JIRA/%s.json % project
  ~pao/site/json/foundation/pmcs.json
  ~pao/site/json/foundation/chairs.json
  ~pao/site/json/projects/%s.json % project

- render.js
  site/reportingcycles.json
  site/getjson.py?only=project
  site/jiraversions.py?project=<pmc>&jiraname=<project>&prepend=<prepend>
  site/addrelease.py?json=true&committee=xxx&version=xxx&date=xxx
