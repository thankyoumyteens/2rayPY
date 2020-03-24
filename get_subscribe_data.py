from urllib.request import ProxyHandler, build_opener
from urllib.request import Request
from urllib.request import urlopen
from urllib.error import URLError
from base64 import b64decode
import subprocess
import socket
import socks
import json
import time
import os


# pip install PySocks

class SubscribeHandler:

    def __init__(self):
        self.urls = []
        current_path = os.path.abspath(__file__)
        self._root_path = os.path.dirname(current_path)
        self._v2ray_path = os.path.join(self._root_path, 'v2ray-linux-64')
        self._vm_list = os.path.join(self._root_path, 'vm_list')
        self._v2ray_processes = None

    def add_subscribe_url(self, subscribe_url):
        self.urls.append(subscribe_url)

    def add_subscribe_urls(self, subscribe_urls):
        self.urls.extend(subscribe_urls)

    def _load_vm_list(self):
        node_list = []
        if not os.path.exists(self._vm_list):
            print('connecting...')
            # load by network
            for u in self.urls:
                node_list.extend(self._update_vm_list(u))
        else:
            # load from local cache
            with open(self._vm_list, 'r', encoding='utf-8') as f_r_vm_list:
                vm_list_str = f_r_vm_list.read()
            lines = vm_list_str.splitlines()
            for line in lines:
                node_list.append(json.loads(line))
        print('node list loaded, size:{}'.format(len(node_list)))
        return node_list

    # get nodes from remote server
    def _update_vm_list(self, subscribe_url):
        res = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        req = Request(url=subscribe_url, headers=headers)
        content = urlopen(req).read().decode()
        # get vmess://......
        links = b64decode(content + '==').decode('utf-8').splitlines()
        # save nodes to file
        if os.path.exists(self._vm_list):
            os.remove(self._vm_list)
        with open(self._vm_list, 'a+', encoding='utf-8') as f_vm_list:
            for link in links:
                # decode vmess protocol to json string
                json_str = b64decode(link.replace('vmess://', '')).decode('utf-8')
                f_vm_list.write(json_str + '\n')
                res.append(json.loads(json_str))
        return res

    # test node status
    def _test_ping(self):
        socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1080)
        socket.socket = socks.socksocket
        try:
            time_start = time.time()
            response = urlopen('https://www.google.com')
            # print(response.read().decode('utf-8'))
            time_end = time.time() # todo...
            return 1
        except URLError as e:
            # print(e.reason)
            return -1

    # update config.json
    def _write_to_config(self, vm):
        with open(os.path.join(self._root_path, 'config.json.template'), 'r', encoding='utf-8') as f_template:
            config_content = f_template.read()
        # $xx is placeholder
        access_log = os.path.join(self._v2ray_path, 'log', 'access.log')
        error_log = os.path.join(self._v2ray_path, 'log', 'error.log')
        config_content = config_content.replace('$ACCESS_LOG', access_log)
        config_content = config_content.replace('$ERROR_LOG', error_log)
        config_content = config_content.replace('$ADDRESS', vm['add'])
        config_content = config_content.replace('$HOST', vm['host'])
        config_content = config_content.replace('$USER_ID', vm['id'])
        config_content = config_content.replace('$NET', '"{}"'.format(vm['net']) if vm['net'] != '' else 'null')
        config_content = config_content.replace('$PATH', vm['path'])
        config_content = config_content.replace('$PORT', vm['port'])
        config_content = config_content.replace('$TLS', '"{}"'.format(vm['tls']) if vm['tls'] != '' else 'null')
        config_json = os.path.join(self._v2ray_path, 'config.json')
        if os.path.exists(config_json):
            os.remove(config_json)
        with open(config_json, 'a+', encoding='utf-8') as f_config_json:
            f_config_json.write(config_content)

    def _run_v2ray(self):
        p = subprocess.Popen('./v2ray-linux-64/v2ray',
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
        self._v2ray_processes = p
        return True

    def _terminate_v2ray(self):
        if self._v2ray_processes:
            self._v2ray_processes.kill()

    def _restart_v2ray(self):
        self._terminate_v2ray()
        self._run_v2ray()

    def start(self):
        nodes = self._load_vm_list()
        if not self._run_v2ray():
            print('run v2ray failed')
            return
        print('testing...')
        sec = self._test_ping()
        print('current delay is {}ms'.format(sec))
        print('*******************************')
        while True:
            op = input('enter q to quit\n')
            if op == 'q':
                print('Bye')
                self._terminate_v2ray()
                return


if __name__ == '__main__':
    with open('url_config', 'r', encoding='utf-8') as f:
        urls = f.read()
    sh = SubscribeHandler()
    for url in urls.splitlines():
        sh.add_subscribe_url(url)
    sh.start()
