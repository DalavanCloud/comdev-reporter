"""
Simple test harness

Reads output from svnpubsub/wacher.py (or similar)
Input is parsed by scandist.processTargets()

If a sufficient gap occurs between commits, then
the parsed data is passed to scandist.processCommit()

TODO: needs to check the output somehow

"""

from __future__ import print_function
import scandist
import json
import ast
import datetime

def processBatch():
    for project in scandist.targets:
        # show what is to be processed
        print("Batch: <<",project, end="~")
        committers = scandist.targets[project]
        for committer in committers:
            print(committer, end="~")
            for entry in committers[committer]:
                print(entry['id'], end="~")
        print(">>")
    scandist.processTargets()
    
if __name__ == "__main__":
    prevdate=None
    scandist.sendEmail = False
    #scandist.trace = True
    scandist.debug = True
    with open("scandist_test.dat") as data:
        inCommit = False
        for line in data:
            if inCommit:
                chunk += line
            if line.startswith("COMMIT:"):
                inCommit = True
                chunk=""
            elif line.endswith("}\n"):
                inCommit = False
                commit = ast.literal_eval(chunk)
                rawDate = commit['date'][:19] # drop the unparseable part (unnecessary for diffs anyway)
                date=datetime.datetime.strptime(rawDate,"%Y-%m-%d %H:%M:%S")# does not seem to support %z??
                if not prevdate == None:
                    diffSecs = (date - prevdate).seconds
                    if diffSecs > 90:
                        processBatch()
                prevdate = date
                scandist.processCommit(commit)

    processBatch() # process any trailing data