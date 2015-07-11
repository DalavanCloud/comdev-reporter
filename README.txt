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

Crontab:
# m h   dom mon dow   command
00 4,12,20 * * * cd /var/www/reporter.apache.org/data && python3.4 parsepmcs.py
00 01      * * * cd /var/www/reporter.apache.org/ && python mailglomper.py
00 09      * * * cd /var/www/reporter.apache.org/ && python readjira.py
00 12      * * * curl "(redacted)" > /var/www/reporter.apache.org/data/mailinglists.json

Scripts:
- data/parsepmcs.py
  creates pmcs.json and projects.json (currently from http://people.apache.org/committer-index.html)

- mailglomper.py
  Updates data/maildata_extended.json from http://mail-archives.us.apache.org/mod_mbox/<list>/<date>.mbox

- readjira.py
  Creates JSON files under /var/www/reporter.apache.org/data/JIRA

  TODO
  - How is site/reportingcycles.json created/maintained?