##############################################################################
#
#  Script: Create VMs on Nutanix Cluster via REST API (v2)
#  Author: Yukiya Shimizu
#  Description: Create VMs on Nutanix Cluster with Cloud-Init
#  Language: Python3
#
##############################################################################

import pprint
import json
import requests
from datetime import datetime
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import paramiko
import warnings
warnings.filterwarnings('ignore')


# v1_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v1/'
# self.v1_url = v1_BASE_URL.format(self.cluster_ip)
v2_BASE_URL = 'https://{}:9440/api/nutanix/v2.0/'
POST = 'post'
GET = 'get'

class NtnxRestApi:
    def __init__(self, cluster_ip, username, password):
        self.cluster_ip = cluster_ip
        self.username = username
        self.password = password
        self.v2_url = v2_BASE_URL.format(self.cluster_ip)
        self.session = self.get_server_session()

    def get_server_session(self):
        # Creating REST client session for server connection, after globally setting.
        # Authorization, content type, and character set for the session.

        session = requests.Session()
        session.auth = (self.username, self.password)
        session.verify = False
        session.headers.update(
            {'Content-Type': 'application/json; charset=utf-8'})
        return session

    def rest_call(self, method_type, sub_url, payload_json):
        if method_type == GET:
            request_url = self.v2_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v2_url + sub_url
            server_response = self.session.post(request_url, payload_json)
        else:
            print("method type is wrong!")
            return

        print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)

    def get_host(self):
        print("host information")
        rest_status, response = self.rest_call(GET, 'hosts', None)
        return rest_status, response

    def get_vmlist(self):
        print("Getting list of VMs")
        rest_status, response = self.rest_call(GET, 'vms', None)

        return rest_status, response

if __name__ == "__main__":

    def get_poweredon_vm(rest_api):
        status, vms = rest_api.get_vmlist()
        vm_list = []
        for entity in vms.get("entities"):
          if(entity.get('power_state') == 'on'):
            vm_list.append(entity.get('name'))
        return vm_list
    
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_cluster_ip = "10.149.161.41"  # Please specify a target cluster external IP Address
        tgt_username = "admin"  # Please specify a user name of target cluster
        tgt_password = "Nutanix/4u!"  # Please specify the password of the user
        rest_api = NtnxRestApi(tgt_cluster_ip, tgt_username, tgt_password)
        # Get Host List
        status,hosts = rest_api.get_host()
        host_list = []
        cvm_list = []
        ipmi_list = []
        for entity in hosts.get("entities"):
          host_list.append(entity.get('hypervisor_address'))
          cvm_list.append(entity.get('controller_vm_backplane_ip'))
          ipmi_list.append(entity.get('ipmi_address'))

        # Shutting Down VMs
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(tgt_cluster_ip, username=tgt_username, password=tgt_password)

        PowerOnVmList = get_poweredon_vm(rest_api)

        PowerOffCheckTimes = 0

        while PowerOffCheckTimes <= 5 :
          if PowerOnVmList:
            PowerOnVmList_Str = ",".join(PowerOnVmList)
            print(PowerOnVmList_Str)
            #command = "acli vm.shutdown {}".format(PowerOnVmList_Str)
            PowerOffCheckTimes += 1
            PowerOnVmList = ['test']
          else:
            print('VM Shutdown successfully completed')
            break
        else:
          print('Shutdown remained VMs forcefully!!')
          print('KILL {}'.format(PowerOnVmList))
          #command = "acli vm.off {}".format(PowerOnVmList_Str)```

    except Exception as ex:
        print(ex)
        exit(1)
