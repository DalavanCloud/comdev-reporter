"""
   Some utilities for working with URLs
"""

import sys
if sys.hexversion < 0x03000000:
    raise ImportError("This script requires Python 3")
import os
from os.path import dirname, abspath, join, getmtime
import shutil
import io
import urllib.request
import time
import calendar

# time format used in Last-Modified/If-Modified-Since HTTP headers
_HTTP_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

"""
   get file mod date in suitable format for If-Modified-Since
   
"""
def mod_date(t):
    return time.strftime(_HTTP_TIME_FORMAT, time.gmtime(t))

"""
   Get a URL if it is not newer

   @param url: the url to fetch
   @param sinceTime: the most recent Last-Modified string
   @param encoding: the encoding to use (default 'None')
   @param errors: If encoding is provided, this specifies the on-error action (e.g. 'ignore')
   @return: (lastMod, response)
   - lastMod: the Last-Modified string
   - response: the HTTPResponse (encoding == None) or TextIOBase object.
    'None' if the URL is not newer
"""
def getIfNewer(url, sinceTime, encoding=None, errors=None):
    if sinceTime:
        headers = {"If-Modified-Since" : sinceTime}
    else:
        headers = {}
    response = None
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        lastMod = resp.headers['Last-Modified']
        if encoding:
            response = io.TextIOWrapper(resp, encoding=encoding, errors=errors)
        else:
            response = resp
    except urllib.error.HTTPError as err:
        if err.code == 304:
            lastMod = sinceTime # preserve timestamp
        else:
            raise
    return lastMod, response

"""
    Creates a cache for URLs
    @param cachedir: the cache directory to use 
        (default data/cache; this is assumed to be at the current directory, its parent or grandparent)
    @param interval: minimum interval between checks for updates to the URL (default 300 secs)
        if set to -1, never checks (intended for testing only)  
    @return: the instance to use with the get() method
"""
class UrlCache(object):
    # get file mod_date
    def __file_mtime(self, filename):
        try:
            t = getmtime(filename)
        except FileNotFoundError:
            t = -1 # so cannot be confused with a valid mtime
        return t

    def __init__(self, cachedir=None, interval=300):
        __CACHE = 'data/cache'
        self.__interval = interval
        self.__cachedir = None
        if cachedir:
            self.__cachedir = cachedir
        else:
            self.__cachedir = __CACHE # will be overwritten if actually found
            for d in ['./','../','../../']: # we may located at same level or 1 or 2 below
                dir = d + __CACHE
                if os.path.isdir(dir):
                    self.__cachedir = dir
                    break
        
        if os.path.isdir(self.__cachedir):
            print("Cachedir: %s" % self.__cachedir)
        else:
            raise OSError("Could not find cache directory '%s'" % self.__cachedir)

    def __getname(self, name):
        return join(self.__cachedir, name)

    def get(self, url, name, encoding=None, errors=None):
        """
            Check if the filename exists in the cache.
            If it does not, or if it does and the URL has not been checked recently,
            then try to download the URL using If-Modified-Since.
            The URL is downloaded to a temporary file and renamed to the filename
            to reduce the time when the file is being updated.
            The interval parameter is used to determine how often to check if the URL has changed.
            (this is mainly intended to avoid excess URL requests in unit testing).
            If this is set to -1, then the URL will only be downloaded once. 
            @param url: the url to fetch (required)
            @param name: the name to use in the cache (required)
            @param encoding: the encoding to use (default None)
            @param errors: If encoding is provided, this specifies the on-error action (e.g. 'ignore')
                        (default None)
            @return: the opened stream, using the encoding if specified. Otherwise opened in binary mode. 
        """
        target=self.__getname(name)
        fileTime = self.__file_mtime(target)
        check = self.__getname("."+name)
        upToDate = False
        if fileTime >= 0:
            if self.__interval == -1:
                print("File %s exists and URL check has been disabled" % name)
                upToDate = True
            else:
                checkTime = self.__file_mtime(check)
                now = time.time()
                diff = now - checkTime
                if diff < self.__interval:
                    print("Recently checked: %d < %d, skip check" % (diff, self.__interval))
                    upToDate = True
                else:
                    print("Not recently checked: %d > %d" % (diff, self.__interval))
        else:
            print("Not found %s " % target)

        if not upToDate:
            sinceTime = mod_date(fileTime)
            lastMod, response = getIfNewer(url, sinceTime)
            if response: # we have a new version
                try:
                    lastModT = calendar.timegm(time.strptime(lastMod, _HTTP_TIME_FORMAT))
                except ValueError:
                    lastModT = 0
                
                tmpFile = target + ".tmp"
                with open(tmpFile,'wb') as f:
                    shutil.copyfileobj(response, f)
                # store the last mod time as the time of the file
                os.utime(tmpFile, times=(lastModT, lastModT))
                os.rename(tmpFile, target) # seems to preserve file mod time
                print("Downloaded new version of %s " % target)
            else:
                print("Cached copy of %s is up to date" % target)

    
            with open(check,'a'):
                os.utime(check, None) # touch the marker file

        if encoding:
            return open(target, 'r', encoding=encoding, errors=errors)
        else:
            return open(target, 'rb')

if __name__ == '__main__':
    fc = UrlCache(cachedir=None,interval=30)
    print("Done")
    