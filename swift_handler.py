#!/usr/bin/python

import urllib2
import json
import openstack_utils
import sys
import confparams_loader

def getContainerList(host,tenID,tok):
    '''print the list of container for this tenant'''
    contList=openstack_utils.AuthenticatedHTTP_GETRequest("https://",host,"8080","/v1/AUTH_"+tenID+"/",tok['id'],responseType="JSON")
    return contList

def getContainerObjects(host,tenID,tok,containerName):
    '''print the list of objects for this container'''
    objList=openstack_utils.AuthenticatedHTTP_GETRequest("https://",host,"8080","/v1/AUTH_"+tenID+"/"+containerName,tok['id'],responseType="JSON")
    return objList

def metadataRead(host,tenID,tok,containerName,objName):
    '''print the data and metadata for this object'''
    md=openstack_utils.AuthenticatedHTTP_GETRequest("https://",host,"8080","/v1/AUTH_"+tenID+"/"+containerName+"/"+objName,tok['id'],responseType="Headers")
    return md

def metadataWrite(swiftObj,tenID,tok,containerName,objName,postDict):
    protocol="https://"
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

    if len(sys.argv) != 5:
        print "some parameters are missing\n"
        print "usage {} {} {} {} {}".format(sys.argv[0],"Container",
                                      "Project","MD-name","MD-value")
        sys.exit(-2)

    tokenHandler=openstack_utils.TokenHandler('https://'+host+':'+port,tenant,user,passwd,token_path)
    swiftHost=host
    tenantID="-1"

    if tokenHandler.getRemainingLifetime() < 300:
        #print "Token is expired"
        tokenHandler.refresh()

    tenants=openstack_utils.AuthenticatedHTTP_GETRequest("https://",host,port,"/v2.0/tenants",tokenHandler.token['id'],responseType="JSON")['tenants']

    for t in tenants:
        if t['name'] == tenant:
            tenantID=t['id']

    if tenantID=="-1":
        print "Unable to find tenant "+tenant+" among those authorized for this token"
        sys.exit(-1)

    containerList=getContainerList(swiftHost,tenantID,tokenHandler.token)
    requestedContainer=sys.argv[1]
    container=[container for container in containerList if container['name']==requestedContainer]
    if not container:
        print "ERROR: Requested container {} is not existing or accessible".format(requestedContainer)
        sys.exit(-1)
    cName=container[0]['name'] # shortcut
    requestedSwObject=sys.argv[2]
    containerObjList=getContainerObjects(swiftHost,tenantID,tokenHandler.token,cName)

    swiftObject=[swObj for swObj in containerObjList if swObj['name']==requestedSwObject]

    if not swiftObject:
        print "Error: Requested swiftObject {} is not existing in this container {}".format(requestedSwObject,cName)
    swObjName=swiftObject[0]['name']

    md=metadataRead(swiftHost,tenantID,tokenHandler.token,cName,swObjName)
    userMD=[(t,md[t]) for t in md if t.startswith('x-object-meta')]
    userMD=dict(userMD)
    metadataValue=sys.argv[4]
    metadataName=sys.argv[3]
    metadataName="x-object-meta-"+metadataName
    metadataName=metadataName.lower()
    # if does not exist, create, else update
    userMD[metadataName]=metadataValue
    #print userMD
    metadataWrite(swiftHost,tenantID,tokenHandler.token,cName,swObjName,userMD)
