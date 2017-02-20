#!/usr/bin/python
"""
Class with methods for interactions with most of OpenStack services
"""

__copyright__ = "Istituto Nazionale di Fisica Nucleare (INFN)"
__license__ = "Apache 2"

import urllib2
import json
import time, calendar
import logging

def AuthenticatedHTTP_GETRequest(protocol,host,port,service,tokenID,responseType=None):

     request=urllib2.Request(protocol+host+":"+port+service)

     request.add_header('X-Auth-Token',tokenID)

     if responseType == 'JSON':
         request.add_header('Content-Type', 'application/json;charset=utf8')
         request.add_header('Accept', 'application/json')

     #print request.get_full_url()

     try :
         response=urllib2.urlopen(request,timeout=2)
         response_data=response.read()

         if responseType == "JSON":
             response_data=json.loads(response_data)
         elif responseType == "Headers":
             response_data=response.info()

         return response_data
     except urllib2.HTTPError,e :
         print "HTTP error :"+str(e.code)
         return -1
     except urllib2.URLError,e :
         print "URL error : "+str(e.reason)
         return -1

def AuthenticatedHTTP_POSTRequest(protocol,host,port,service,tokenID,postItemsDict):
     ''' Supports pairs of items to be inserted as headers for the post request'''

     request=urllib2.Request(protocol+host+":"+port+service)
     request.add_header('X-Auth-Token',tokenID)

     for key in postItemsDict:
         request.add_header(key,postItemsDict[key])

     ''' this turn get in post'''
     request.add_data('')
     #print request.get_full_url()
     #print request.header_items()
     try :
         response=urllib2.urlopen(request)
         return 0
     except urllib2.HTTPError,e :
         print "HTTP error {} {}".format(str(e.code),str(e.reason))
     except urllib2.URLError,e :
         print "URL error : "+str(e.reason)

     print "excepted"
     return -1

class TokenHandler:
    """
    This class provides means to requests and manage authentication tokens
    """
    def __init__(self,keystoneEndpoint,adminTenant,adminUser,adminPassword,filePath):
        """ initialize the token sourcing a given file path """
        self.tokenFilePath=filePath
        self.endpoint=keystoneEndpoint
        self.tenant=adminTenant
        self.user=adminUser
        self.password=adminPassword
        self.token=self.readFile()

    def getRemainingLifetime(self):
        """ return token remaining lifetime """

        now=time.time()
        expire_time=self.token['expires']
        return expire_time - now

    def refresh(self):
        """ write token to the file """
        #print "Trying to write a new token"

        tokenFile=open(self.tokenFilePath,'w')
        self.token=self.getToken()
        json.dump(self.token,tokenFile)
        tokenFile.close()
        return self.token

    def readFile(self):
        """ read the token from file """

        token=""

        try :
            tokenFile=open(self.tokenFilePath,'r')
            token=json.load(tokenFile)
            #print "token successfully loaded from %s" %(self.tokenFilePath)
            tokenFile.close()
        except IOError as e:
            #print "Unable to open %s : %s" %(self.tokenFilePath,e.strerror)
            token=self.refresh()
        except ValueError as e:
            #print "Unable to read token from %s" %(self.tokenFilePath)
            token=self.refresh()

        return token

    def getToken(self):
        """ actually contact keystone and grabs the token
        :returns a tuple with
         - the Keystone token assigned to these credentials a
         - the expiration time (to avoid API REST calls at each iteration)
        """

        auth_request = urllib2.Request(self.endpoint+"/v2.0/tokens")
        auth_request.add_header('Content-Type', 'application/json;charset=utf8')
        auth_request.add_header('Accept', 'application/json')
        auth_data = {"auth": {"tenantName": self.tenant, "passwordCredentials": {"username": self.user, "password": self.password}}}
        auth_request.add_data(json.dumps(auth_data))
        auth_response = urllib2.urlopen(auth_request)
        response_data = json.loads(auth_response.read())

        token_id = response_data['access']['token']['id']
        expiration_time = response_data['access']['token']['expires']
        #self.logger.debug("Token expiration time:" + expiration_time)
        expiration_timestamp = calendar.timegm(time.strptime(expiration_time,"%Y-%m-%dT%H:%M:%SZ"))
        #self.logger.debug("Expiration timestamp: " + str(expiration_timestamp))

        token = {'id': token_id, 'expires': expiration_timestamp}

        return token
