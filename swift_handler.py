#!/usr/bin/python

import urllib2
import json
import openstack_utils
import sys
import confparams_loader

def getContainerList(host,tenID,tok):
    '''print the list of container for this tenant'''
    contList=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8080","/v1/AUTH_"+tenID+"/",tok['id'],responseType="JSON")
    return contList

def getContainerObjects(host,tenID,tok,containerName):
    '''print the list of objects for this container'''
    objList=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8080","/v1/AUTH_"+tenID+"/"+containerName,tok['id'],responseType="JSON")
    return objList

def metadataRead(host,tenID,tok,containerName,objName):
    '''print the data and metadata for this object'''
    md=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8080","/v1/AUTH_"+tenID+"/"+containerName+"/"+objName,tok['id'])
    return md

def metadataWrite(swiftObj,tenID,tok,containerName,objName,postDict):
    protocol="http://"
    port="8080"
    objectPath="/v1/AUTH_"+tenID+"/"+containerName+"/"+objName
    md=openstack_utils.AuthenticatedHTTP_POSTRequest(protocol,host,port,objectPath,tok['id'],postDict)
    return md

if __name__ == '__main__':

    confParams=confparams_loader.ReadConfFile("user-params.txt")
    host=confParams.read_option('host')
    port=confParams.read_option('port')
    tenant=confParams.read_option('admin_tenant')
    user=confParams.read_option('admin_user')
    passwd=confParams.read_option('passwd')
    token_path=confParams.read_option('token_path')

    tokenHandler=openstack_utils.TokenHandler('https://'+host+':'+port,tenant,user,passwd,token_path)
    swiftHost=host
    tenantID="-1"
    
    if tokenHandler.getRemainingLifetime() < 300:
        #print "Token is expired"
        tokenHandler.refresh()       
    
    tenants=openstack_utils.AuthenticatedHTTP_GETRequest("https://",host,port,"/v2.0/tenants",tokenHandler.token['id'],responseType="JSON")['tenants']
    # a token could be valid for more than one tenant 

    for t in tenants:
        if t['name'] == tenant:
            tenantID=t['id']
    
    if tenantID=="-1":
        print "Unable to find tenant "+tenant+" among those authorized for this token"
        sys.exit(-1)

    containerList=getContainerList(swiftHost,tenantID,tokenHandler.token)
    
    # prendi il primo container
    containerName=containerList[0]['name']
    containerObjList=getContainerObjects(swiftHost,tenantID,tokenHandler.token,containerName)
    # prendi il primo oggetto
    swiftObject=containerObjList[0]['name']
    print swiftObject
    # in questo test swiftObject e' il primo oggetto del primo container
    md=metadataRead(swiftHost,tenantID,tokenHandler.token,containerName,swiftObject)
    print "File content:\n-------\n"+md+"-------\n"
    metadataValue=sys.argv[1]
    metadataName="X-Object-Meta-Book"
    postDict={metadataName:metadataValue}
    metadataWrite(swiftHost,tenantID,tokenHandler.token,containerName,swiftObject,postDict)
    
