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
00 4,12,20 * * * cd /var/www/reporter.apache.org/data && python3.4 parsepmcs.py
00 01 * * * cd /var/www/reporter.apache.org/ && python mailglomper.py
00 09 * * * cd /var/www/reporter.apache.org/ && python readjira.py
00 12 * * * curl "(removed)" > /var/www/reporter.apache.org/data/mailinglists.json


TODO:
- where are the scripts that populate the data files?
- the data/ files seem to be static; are they ever updated?