#!/usr/bin/env python

#################################################
# scandist.py: a minimalistic svnwcsub program  #
#################################################

from threading import Thread
from datetime import datetime
import os
import sys


# SMTP Lib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

version = 2
if sys.hexversion < 0x03000000:
    print("Using Python 2...")
    import json, httplib, urllib, urllib2, ConfigParser as configparser, re, base64, sys, os, time, atexit, signal, logging, socket, subprocess
    socket._fileobject.default_bufsize = 0
else:
    print("Using Python 3")
    version = 3
    import json, http.client, urllib.request, urllib.parse, configparser, re, base64, sys, os, time, atexit, signal, logging, subprocess

targets = {} # dict: key = project name, value = list of commits for the project

###########################################################
# Daemon class, curtesy of an anonymous good-hearted soul #
###########################################################
class daemon:
        """A generic daemon class.

        Usage: subclass the daemon class and override the run() method."""

        def __init__(self, pidfile): self.pidfile = pidfile
        
        def daemonize(self):
                """Deamonize class. UNIX double fork mechanism."""

                try: 
                        pid = os.fork() 
                        if pid > 0:
                                # exit first parent
                                sys.exit(0) 
                except OSError as err: 
                        sys.stderr.write('fork #1 failed: {0}\n'.format(err))
                        sys.exit(1)
        
                # decouple from parent environment
                os.chdir('/') 
                os.setsid() 
                os.umask(0) 
        
                # do second fork
                try: 
                        pid = os.fork() 
                        if pid > 0:

                                # exit from second parent
                                sys.exit(0) 
                except OSError as err: 
                        sys.stderr.write('fork #2 failed: {0}\n'.format(err))
                        sys.exit(1) 
        
                # redirect standard file descriptors
                sys.stdout.flush()
                sys.stderr.flush()
                si = open(os.devnull, 'r')
                so = open(os.devnull, 'a+')
                se = open(os.devnull, 'a+')

                os.dup2(si.fileno(), sys.stdin.fileno())
                os.dup2(so.fileno(), sys.stdout.fileno())
                os.dup2(se.fileno(), sys.stderr.fileno())
        
                # write pidfile
                atexit.register(self.delpid)

                pid = str(os.getpid())
                with open(self.pidfile,'w+') as f:
                        f.write(pid + '\n')
        
        def delpid(self):
                os.remove(self.pidfile)

        def start(self):
                """Start the daemon."""

                # Check for a pidfile to see if the daemon already runs
                try:
                        with open(self.pidfile,'r') as pf:

                                pid = int(pf.read().strip())
                except IOError:
                        pid = None
        
                if pid:
                        message = "pidfile {0} already exist. " + \
                                        "Daemon already running?\n"
                        sys.stderr.write(message.format(self.pidfile))
                        sys.exit(1)
                
                # Start the daemon
                self.daemonize()
                self.run()

        def stop(self):
                """Stop the daemon."""

                # Get the pid from the pidfile
                try:
                        with open(self.pidfile,'r') as pf:
                                pid = int(pf.read().strip())
                except IOError:
                        pid = None
        
                if not pid:
                        message = "pidfile {0} does not exist. " + \
                                        "Daemon not running?\n"
                        sys.stderr.write(message.format(self.pidfile))
                        return # not an error in a restart

                # Try killing the daemon process        
                try:
                        while 1:
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.1)
                except OSError as err:
                        e = str(err.args)
                        if e.find("No such process") > 0:
                                if os.path.exists(self.pidfile):
                                        os.remove(self.pidfile)
                        else:
                                print (str(err.args))
                                sys.exit(1)

        def restart(self):
                """Restart the daemon."""
                self.stop()
                self.start()

        def run(self):
                """You should override this method when you subclass Daemon.
                
                It will be called after the process has been daemonized by 
                start() or restart()."""



####################
# Helper functions #
####################


# read_chunk: iterator for reading chunks from the stream
# since this is all handled via urllib now, this is quite rudimentary
def read_chunk(req):
    while True:
        try:
            line = req.readline().strip()
            if line:
                yield line
            else:
                print("No more lines?")
                break
        except Exception as info:
            
            break
    return

 
#########################
# Main listener program #
#########################



# PubSub class: handles connecting to a pubsub service and checking commits
class PubSubClient(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True) # ensure script exits when main process is killed with ^C

    def run(self):
        global targets
        while True:
            
            self.req = None
            while not self.req:
                try:
                    if version == 3:
                        self.req = urllib.request.urlopen(self.url, None, 30)
                    else:
                        self.req = urllib2.urlopen(self.url, None, 30)
                    
                except:
                    
                    time.sleep(30)
                    continue
                
            for line in read_chunk(self.req):
                if version == 3:
                    line = str( line, encoding='ascii' ).rstrip('\r\n,').replace('\x00','') # strip away any old pre-0.9 commas from gitpubsub chunks and \0 in svnpubsub chunks
                else:
                    line = str( line ).rstrip('\r\n,').replace('\x00','') # strip away any old pre-0.9 commas from gitpubsub chunks and \0 in svnpubsub chunks
                try:
                    obj = json.loads(line)
                    if "commit" in obj and "repository" in obj['commit']:
                        if 'changed' in obj['commit']:
                        
                            #Grab some vars
                            commit = obj['commit']
                            # e.g. {"committer": "sebb", "log": "Ensure we exit on control+C", "repository": "13f79535-47bb-0310-9956-ffa450edef68", "format": 1, 
                            # "changed": {"comdev/reporter.apache.org/trunk/scandist.py": {"flags": "U  "}}, 
                            # "date": "2015-07-13 13:38:33 +0000 (Mon, 13 Jul 2015)", "type": "svn", "id": 1690668}

                            # Note: a single commit can change multiple paths
                            for path in commit['changed']:
                                # Is it a dist/release commit?
                                match = re.match(r"^release/([a-z0-9]+)", path)
                                if match:
                                    project = match.group(1) 
                                    if project != "incubator":
                                        # a single commit can potentially affect multiple projects
                                        # create the array if necessary
                                        if not project in targets:
                                            targets[project] = []
                                        # would like to use a set, but cannot add dicts to sets
                                        if not commit in targets[project]: 
                                            targets[project].append(commit)


                except ValueError as detail:
                    continue
            




################         
# Main program #
################

"""
According to https://svn.apache.org/repos/asf/subversion/trunk/tools/server-side/svnpubsub/svnpubsub/server.py

#   URLs are constructed from 3 parts:
#       /${notification}/${optional_type}/${optional_repository}
#
#   Notifications can be sent for commits or metadata (e.g., revprop) changes.
#   If the type is included in the URL, you will only get notifications of that type.
#   The type can be * and then you will receive notifications of any type.
#
#   If the repository is included in the URL, you will only receive
#   messages about that repository.  The repository can be * and then you
#   will receive messages about all repositories.

"""

def main():
    global targets
    if debug:
        print("Foreground test mode enabled, no updates will be made")
        
  
    
    # Start the svn thread
    svn_thread = PubSubClient()
    # 0d268c88-bc11-4956-87df-91683dc98e59 = https://dist.apache.org/repos/dist
    svn_thread.url = "http://hades.apache.org:2069/commits/svn/0d268c88-bc11-4956-87df-91683dc98e59"
    svn_thread.start()
    
    while True:
        if debug:
           time.sleep(20)
        else:
           time.sleep(600)
        targetstwo = targets
        targets = {}
        sender = 'no-reply@reporter.apache.org'
        for project in targetstwo:
            #print("targetstwo[project] = %s" % targetstwo[project])
            for commit in targetstwo[project]:
                #print("commit = %s" % commit)
                tmpdict = {'project' : project}
                #print("tmpdict = %s" % tmpdict)
                tmpdict.update(commit) # add project without corrupting commit
                #print("tmpdict = %s" % tmpdict)
                # e.g. {"committer": "sebb", "log": "Ensure we exit on control+C", "repository": "13f79535-47bb-0310-9956-ffa450edef68", "format": 1, 
                # "changed": {"comdev/reporter.apache.org/trunk/scandist.py": {"flags": "U  "}}, 
                # "date": "2015-07-13 13:38:33 +0000 (Mon, 13 Jul 2015)", "type": "svn", "id": 1690668}
                email = commit['committer'] + "@apache.org"
                receivers = [email, 'sebb@apache.org']
                print "Notifying %(committer)s of new data pushed to %(project)s in r%(id)s" % tmpdict
                message = """From: Apache Reporter Service <no-reply@reporter.apache.org>
To: %(committer)s <%(committer)s.apache.org>
Reply-To: dev@community.apache.org
Subject: Please add your release data for '%(project)s'

Hi,
This is an automated email from reporter.apache.org.
I see that you just pushed something to our release repository for the %(project)s project.

If you are a PMC member of this project, we ask that you log on to:
https://reporter.apache.org/addrelease.html?%(project)s
and add your release data (version and date) to the database.

If you are not a PMC member, please have a PMC member add this information.

While this is not a requirement, we ask that you still add this data to the
reporter database, so that people using the Apache Reporter Service will be
able to see the latest release data for this project.

With regards,
The Apache Reporter Service.
                """ % tmpdict;
            
                try:
                   smtpObj = smtplib.SMTP('localhost')
                   smtpObj.sendmail(sender, receivers, message)  
                   #print message       
                   print "Successfully sent email"
                except Exception as ex:
                   print "Error: unable to send email", ex


##############
# Daemonizer #
##############
class MyDaemon(daemon):
    def run(self):
        main()
 
if __name__ == "__main__":
        daemon = MyDaemon('/tmp/scandist.pid')
        if len(sys.argv) >= 2:
                if 'start' == sys.argv[1]:
                    daemon.start()
                elif 'stop' == sys.argv[1]:
                    daemon.stop()
                elif 'restart' == sys.argv[1]:
                    daemon.restart()
                elif 'foreground' == sys.argv[1]:
                    debug = True
                    main()
                else:
                    print("Unknown command")
                    sys.exit(2)
                sys.exit(0)
        else:
                print("usage: %s start|stop|restart|foreground" % sys.argv[0])
                sys.exit(2)

