This directory contains both scripts (which are stored in SVN)
and JSON files (which are not, because they are recreated on demand)

Note that the JIRA subdirectory contents can be recreated on demand
However the releases and history subdirectories contain json files
that are maintained on the server, so need to be saved to SVN
This means that those directories need to be writable by the projects_role SVN login

Note: it is intended to store the committee and committer history files here
However at present these contain timestamps in every entry which would mean
every update would need to be committed, generating a lot of unnecessary mail.
The intention is to rewrite the script to fix this, and also to fetch the
data from LDAP and Git instead scraping the people.a.o website
