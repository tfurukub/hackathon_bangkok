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


v1_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v1/'
# self.v1_url = v1_BASE_URL.format(self.cluster_ip)
v2_BASE_URL = 'https://{}:9440/api/nutanix/v2.0/'
v3_BASE_URL = 'https://{}:9440/api/nutanix/v3/'
POST = 'post'
GET = 'get'

class NtnxRestApi:
    def __init__(self, cluster_ip, username, password):
        self.cluster_ip = cluster_ip
        self.username = username
        self.password = password
        self.v2_url = v2_BASE_URL.format(self.cluster_ip)
        self.v1_url = v1_BASE_URL.format(self.cluster_ip)
        self.v3_url = v3_BASE_URL.format(self.cluster_ip)
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

    def rest_call_v1(self, method_type, sub_url, payload_json):
        if method_type == GET:
            request_url = self.v1_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v1_url + sub_url
            server_response = self.session.post(request_url, payload_json)
        else:
            print("method type is wrong!")
            return

        print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)

    def rest_call_v3(self, method_type, sub_url, payload_json):
        if method_type == GET:
            request_url = self.v3_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v3_url + sub_url
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
        rest_status, response = self.rest_call(GET, 'vms/?include_vm_nic_config=true', None)
        return rest_status, response

    def get_multicluster(self):
        print("Check PC registration")
        rest_status, response = self.rest_call_v1(GET, 'multicluster/cluster_external_state', None)
        return rest_status, response

    def get_fsvm(self):
        print("Check FSVM")
        rest_status, response = self.rest_call_v1(GET, 'vfilers', None)
        return rest_status, response

    def get_app(self):
        print("Get app list")
        rest_status, response = self.rest_call_v3(POST, '/apps/list', '{}')
        #print(json.dumps(response))
        return rest_status, response

    def get_stop_uuid(self,app_uuid):
        print("Get stop uuid")
        stop_uuid_list = {}
        app_name_list = {}
        for uuid in app_uuid:
            rest_status, response = self.rest_call_v3(GET,'/apps/'+uuid,None)
            app_name_list[uuid] = response['status']['resources']['action_list'][0]['runbook']['task_definition_list'][0]['target_any_local_reference']['name']
            for action in response['status']['resources']['action_list']:
                if action['name'] == 'action_stop':
                    stop_uuid_list[uuid] = action['uuid']

        return app_name_list,stop_uuid_list

    def run_stop(self,app_name,stop_uuid):
        print("Stop App")
        for app_uuid in stop_uuid:
            print(app_uuid,stop_uuid[app_uuid])
            payload = {"api_version":"3.0","metadata":{"project_reference":{"kind":"project","name":"default","uuid":"a461190c-0cb8-4478-9575-30746955e076"},"name":"test1","creation_time":"1552450617838941","spec_version":3,"kind":"app","last_update_time":"1552450743657839","uuid":"a24a33d7-72d7-c560-4de4-cb80252aaf4e","categories":{"TemplateType":"Vm"}},"spec":{"target_uuid":app_uuid,"target_kind":"Application","args":[]}}
            rest_status, response = self.rest_call_v3(POST,'/apps/'+app_uuid+'/actions/'+stop_uuid[app_uuid]+'/run',json.dumps(payload))
        return rest_status,response


if __name__ == "__main__":

    def get_poweredon_vm(rest_api):
        status, vms = rest_api.get_vmlist()
        vm_list = []
        for entity in vms.get("entities"):
          if(entity.get('power_state') == 'on'):
            vm_list.append(entity.get('name'))
        return vm_list

    def check_pc(rest_api):
        status, response = rest_api.get_multicluster()
        if len(response) > 0:
            pc_ip = str(response[0].get('clusterDetails').get('ipAddresses')[0])

        status, vms = rest_api.get_vmlist()
        pc_name = []
        for entity in vms.get("entities"):
            if len(entity.get('vm_nics')) > 0:
                vm_ip = entity.get('vm_nics')[0].get('ip_address')
                #print(vm_ip)
                if vm_ip == pc_ip:
                    pc_name.append(entity.get('name'))

        return pc_name
      
    def check_fsvm(rest_api):
        status, fsvm = rest_api.get_fsvm()
        fsvm_list = []
        for entity in fsvm.get('entities'):
            for nvms in entity.get('nvms'):
                fsvm_list.append(nvms.get('name'))
        return fsvm_list

    def stop_app(rest_api_pc):
        status, response = rest_api_pc.get_app()
        app_uuid = []
        for entity in response['entities']:
            app_uuid.append(entity['status']['uuid'])
        app_name,stop_uuid = rest_api_pc.get_stop_uuid(app_uuid)
        status, response = rest_api_pc.run_stop(app_name,stop_uuid)
        return status, response
    
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_cluster_ip = "10.149.161.41"  # Please specify a target cluster external IP Address
        tgt_pc_ip = "10.149.161.42"  # Please specify a target cluster external IP Address
        tgt_username = "admin"  # Please specify a user name of target cluster
        tgt_password = "Nutanix/4u!"  # Please specify the password of the user
        rest_api = NtnxRestApi(tgt_cluster_ip, tgt_username, tgt_password)
        rest_api_pc = NtnxRestApi(tgt_pc_ip,tgt_username,tgt_password)

        # Get Host List
        status,hosts = rest_api.get_host()
        host_list = []
        cvm_list = []
        ipmi_list = []
        for entity in hosts.get("entities"):
          host_list.append(entity.get('hypervisor_address'))
          cvm_list.append(entity.get('controller_vm_backplane_ip'))
          ipmi_list.append(entity.get('ipmi_address'))

        # Check Calm
        status, respose = stop_app(rest_api_pc) 
        # Check PC registration
        pc_name = check_pc(rest_api)
        print("PC name = {}".format(pc_name))

        # Check FSVM
        fsvm_name = check_fsvm(rest_api)
        print("FSVM name = {}".format(fsvm_name))
        # Shutting Down VMs
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(tgt_cluster_ip, username=tgt_username, password=tgt_password)


        def get_list_uvm_state_on():
          list_vm_state_on = get_poweredon_vm(rest_api)
          list_pcvm = pc_name
          list_fsvm = fsvm_name
          list_pcvm_fsvm = list_pcvm + list_fsvm
          # Remove PCVM and FSVM from List
          list_uvm_state_on = [n for n in list_vm_state_on if n not in list_pcvm_fsvm]
          return list_uvm_state_on

        list_uvm_state_on = get_list_uvm_state_on()

        MAX_CHECK_POWREDOFF = 5
        times_check_powredoff = 0

        while times_check_powredoff <= MAX_CHECK_POWREDOFF :
          if list_uvm_state_on:
            list_uvm_state_on_str = ",".join(list_uvm_state_on)
            #print(list_uvm_state_on_str)
            #command = "acli vm.shutdown {}".format(list_uvm_state_on_str)
            times_check_powredoff += 1
            #list_uvm_state_on = get_list_uvm_state_on()
          else:
            print('Guest VM Shutdown has successfully completed')
            break
        else:
          print('Power-off remained Guest VMs forcefully!!')
          print('KILL {}'.format(list_uvm_state_on))
          #command = "acli vm.off {}".format(list_uvm_state_on_str)

    except Exception as ex:
        print(ex)
        exit(1)
