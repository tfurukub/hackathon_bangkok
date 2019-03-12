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

    def get_cluster_info(self):
        print("Getting cluster information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'clusters', None)

        with open('cluster.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def get_host(self):
        print("host information")
        rest_status, response = self.rest_call(GET, 'hosts', None)
        return rest_status, response

    def get_cluster_info(self):
        print("Getting cluster information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'clusters', None)

        with open('cluster.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def get_vmlist(self):
        print("Getting list of VMs")
        rest_status, response = self.rest_call(GET, 'vms', None)

        return rest_status, response

    def get_networks_info(self):
        print("Getting networks information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'networks', None)

        with open('networks.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def get_vm_perf(self,vm_uuid,start,end,interval):
        sub_url = "vms/"+vm_uuid+"/stats"+"/?metrics=hypervisor_cpu_usage_ppm%2Cmemory_usage_ppm&startTimeInUsecs="+start+"&endTimeInUsecs="+end+"&intervalInSecs="+interval
        rest_status, response = self.rest_call(GET,sub_url,None)
        return rest_status, response


if __name__ == "__main__":
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

        print(host_list,cvm_list,ipmi_list)

        # Get VM List
        status, vms = rest_api.get_vmlist()
        print(vms) 

    except Exception as ex:
        print(ex)
        exit(1)
