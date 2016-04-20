#!/usr/bin/python

import urllib2
import json
import openstack_utils
import sys
import confparams_loader

def getHypervisorsList(token):
    '''prints the list of nodes'''
    hypervisorList=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8774","/v2/"+tenantID+"/os-hypervisors",token['id'],responseType="JSON") 
    return hypervisorList

def getHypervisorDetails(token,hvID):
    '''return all details for a node'''
    hvDetails=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8774","/v2/"+tenantID+"/os-hypervisors/"+str(hvID),token['id'],responseType="JSON")
    return hvDetails['hypervisor']

def getHypervisorUptime(token,hvID):

    '''there's no proper entry for host workload. But the output of uptime, 
    to be eventually parsed, is provided'''

    import re
    request=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,"8774","/v2/"+tenantID+"/os-hypervisors/"+str(hvID)+"/uptime",token['id'],responseType="JSON")
    uptime=request['hypervisor']['uptime']
    loadAvgs=[]

    try :

        m=re.search('load average: (\d.+\d\d), (\d.+\d\d), (\d.+\d\d)',uptime)
        loadAvgs.append(m.group(1))
        loadAvgs.append(m.group(2))
        loadAvgs.append(m.group(3))
    except AttributeError:
        print "Unable to parse correctly request output, return values are not valid"
        loadAvgs=[-1,-1,-1]

    return loadAvgs

def renderHypervisorInfo(hvDetail,hvLoad):
    '''pack the requested info in a new dict, to be exposed for zabbix queries'''
  
    packedInfo={}
    
    totalCPUs=hvDetail['vcpus']
    
    # Normalize by number of CPUs
    hvLoad=[float(val)/totalCPUs for val in hvLoad]
    packedInfo['HypervisorLoad1mAvg']=hvLoad[0]
    packedInfo['HypervisorLoad5mAvg']=hvLoad[1]
    packedInfo['HypervisorLoad15mAvg']=hvLoad[2]
    mem_percentage_use=(float(hvDetail['memory_mb_used'])/float(hvDetail['memory_mb']))
    packedInfo['MemoryUsage']=mem_percentage_use
    packedInfo['RunningVMS']=hvDetail['running_vms']
    packedInfo['CPUsFree']=totalCPUs - hvDetail['vcpus_used']
    packedInfo['DiskFree']=hvDetail['disk_available_least']
    
    return packedInfo

def showUsage():
    msg="These modules print some information related to nova nodes"
    msg+="(hypervisors in the beginning).\n"
    msg+="Usage:"+sys.argv[0]+" ComputeNodename RequestedInfo\n"
    msg+="Requested info can be one of the following:\n" 
    msg+="HypervisorLoad1mAvg HypervisorLoad5mAvg HypervisorLoad15mAvg "
    msg+="MemoryUsage RunningVMS CPUsFree DiskFree\n"
    print msg

if __name__ == '__main__':

    confParams=confparams_loader.ReadConfFile("os-params.txt")
    host=confParams.read_option('host')
    port=confParams.read_option('port')
    admin_tenant=confParams.read_option('admin_tenant')
    admin_user=confParams.read_option('admin_user')
    passwd=confParams.read_option('passwd')
    token_path=confParams.read_option('token_path')


    nodeNameId={}
    keystoneUrl='http://'+host+':'+port
    #print keystoneUrl
    tokenHandler=openstack_utils.TokenHandler(keystoneUrl,admin_tenant,admin_user,passwd,token_path)
    #showUsage() 
   
    if tokenHandler.getRemainingLifetime() < 300:
        #print "Token is expired"
        tokenHandler.refresh()   
    
    tenantID=openstack_utils.AuthenticatedHTTP_GETRequest("http://",host,port,"/v2.0/tenants",tokenHandler.token['id'],responseType="JSON")['tenants'][0]['id']
    
    hypervisors=getHypervisorsList(tokenHandler.token)
    #print hypervisors

    for hv in hypervisors['hypervisors']:
        nodeNameId[hv['hypervisor_hostname']]=hv['id']
        
    
    try:  
        hypervisorID=nodeNameId[sys.argv[1]]
    except KeyError:
        print "'%s' not found among computing nodes" %(sys.argv[1])
        sys.exit(-1)

    hypervisorDetails=getHypervisorDetails(tokenHandler.token,hypervisorID)
    hypervisorLoad=getHypervisorUptime(tokenHandler.token,hypervisorID)
    renderedInfo=renderHypervisorInfo(hypervisorDetails,hypervisorLoad)
    print renderedInfo[sys.argv[2]]
