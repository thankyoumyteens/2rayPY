from urllib.request import Request
from urllib.request import urlopen
from base64 import b64decode
import subprocess
import json
import os


# "access": "$ACCESS_LOG"
# "error": "$ERROR_LOG"
# "add": "$ADDRESS"
# "host": "$HOST"
# "id": "$USER_ID"
# "net": $NET
# "path": "$PATH"
# "port": $PORT
# "ps": "Holy-JP-NTT"
# "tls": $TLS
# "v": 2,
# "aid": 0,
# "type": "none"
class SubscribeHandler:

    def __init__(self, url):
        self.url = url
        current_path = os.path.abspath(__file__)
        self.root_path = os.path.dirname(current_path)
        self.v2ray_path = os.path.join(self.root_path, 'v2ray-linux-64')

    # get nodes from remote server
    def update_vm_list(self):
        res = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        req = Request(url=self.url, headers=headers)
        content = urlopen(req).read().decode()
        # get vmess://......
        links = b64decode(content + '==').decode('utf-8').splitlines()
        # save nodes to file
        vm_list = os.path.join(self.root_path, 'vm_list')
        if os.path.exists(vm_list):
            os.remove(vm_list)
        f = open(vm_list, 'a+', encoding='utf-8')
        for link in links:
            # decode vmess protocol to json string
            json_str = b64decode(link.replace('vmess://', '')).decode('utf-8')
            f.write(json_str + '\n')
            res.append(json.loads(json_str))
        f.close()
        return res

    # test node status
    def test_ping(self, vm):
        pass

    # update config.json
    def write_to_config(self, vm):
        f_t = open(os.path.join(self.root_path, 'config.json.template'), 'r', encoding='utf-8')
        config_content = f_t.read()
        f_t.close()
        # $xx is placeholder
        access_log = os.path.join(self.v2ray_path, 'log', 'access.log')
        error_log = os.path.join(self.v2ray_path, 'log', 'error.log')
        config_content = config_content.replace('$ACCESS_LOG', access_log)
        config_content = config_content.replace('$ERROR_LOG', error_log)
        config_content = config_content.replace('$ADDRESS', vm['add'])
        config_content = config_content.replace('$HOST', vm['host'])
        config_content = config_content.replace('$USER_ID', vm['id'])
        config_content = config_content.replace('$NET', '"{}"'.format(vm['net']) if vm['net'] != '' else 'null')
        config_content = config_content.replace('$PATH', vm['path'])
        config_content = config_content.replace('$PORT', vm['port'])
        config_content = config_content.replace('$TLS', '"{}"'.format(vm['tls']) if vm['tls'] != '' else 'null')
        config_json = os.path.join(self.v2ray_path, 'config.json')
        if os.path.exists(config_json):
            os.remove(config_json)
        f = open(config_json, 'a+', encoding='utf-8')
        f.write(config_content)
        f.close()

    def start(self):
        out = subprocess.check_output('./v2ray-linux-64/v2ray').decode('utf-8')
        while True:
            op = input('enter q to quit')
            if op == 'q':
                # todo close v2ray process
                return


if __name__ == '__main__':
    pass
