from urllib.request import urlopen
from urllib.request import Request
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
        current_path = os.path.abspath(__file__)
        with open('url_config', 'r', encoding='utf-8') as f:
            urls = f.read()
        self.urls = []
        for url in urls.splitlines():
            self.urls.append(url)
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
        print('connecting {}'.format(subscribe_url))
        res = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        req = Request(url=subscribe_url, headers=headers)
        content = urlopen(req).read().decode()
        # get vmess://......
        links = b64decode(content + '==').decode('utf-8').splitlines()
        # save nodes to file
        with open(self._vm_list, 'a+', encoding='utf-8') as f_vm_list:
            for link in links:
                # decode vmess protocol to json string
                json_str = b64decode(link.replace('vmess://', '')).decode('utf-8')
                f_vm_list.write(json_str + '\n')
                res.append(json.loads(json_str))
        return res

    # test node status
    def _test_ping(self, node=None):
        if node:
            self._write_to_config(node)
        socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1080)
        socket.socket = socks.socksocket
        try:
            time_start = time.time()
            response = urlopen('https://www.google.com', timeout=3)
            # print(response.read().decode('utf-8'))
            time_end = time.time()  # todo...
            return time_end - time_start
        except URLError:
            # print(e.reason)
            return -1

    # update config.json
    def _write_to_config(self, target_node):
        self._terminate_v2ray()
        with open(os.path.join(self._root_path, 'config.json.template'), 'r', encoding='utf-8') as f_template:
            config_content = f_template.read()
        # $xx is placeholder
        access_log = os.path.join(self._v2ray_path, 'log', 'access.log')
        error_log = os.path.join(self._v2ray_path, 'log', 'error.log')
        config_content = config_content.replace('$ACCESS_LOG', access_log)
        config_content = config_content.replace('$ERROR_LOG', error_log)
        config_content = config_content.replace('$ADDRESS', target_node['add'])
        config_content = config_content.replace('$HOST', target_node['host'])
        config_content = config_content.replace('$USER_ID', target_node['id'])
        config_content = config_content.replace('$NET', '"{}"'.format(
            target_node['net']) if target_node['net'] != '' else 'null')
        config_content = config_content.replace('$PATH', target_node['path'])
        config_content = config_content.replace('$PORT', target_node['port'])
        config_content = config_content.replace('$TLS', '"{}"'.format(
            target_node['tls']) if target_node['tls'] != '' else 'null')
        config_json = os.path.join(self._v2ray_path, 'config.json')
        if os.path.exists(config_json):
            os.remove(config_json)
        with open(config_json, 'a+', encoding='utf-8') as f_config_json:
            f_config_json.write(config_content)
        self._run_v2ray()
        time.sleep(1)

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

    @staticmethod
    def _print_functions():
        print('===========menu==========\n')
        print('1: update node list\n')
        print('2: ping node list\n')
        print('3: use the fastest node\n')

    def start(self):
        nodes = self._load_vm_list()
        nodes_delay = {}
        if not self._run_v2ray():
            print('run v2ray failed')
            return
        print('testing...')
        time.sleep(1)  # wait process run
        sec = self._test_ping()
        print('current delay is {}ms'.format(sec))
        print('*******************************')
        while True:
            op = input('enter q to quit, h to show functions\n')
            if op == 'q':
                print('Bye')
                self._terminate_v2ray()
                return
            elif op == 'h':
                self._print_functions()
            elif op == '1':
                print('updating...')
                if os.path.exists(self._vm_list):
                    os.remove(self._vm_list)
                nodes = self._load_vm_list()
            elif op == '2':
                with open('test_ping', 'w', encoding='utf-8') as f:
                    for node in nodes:
                        print('testing {}'.format(node['add']))
                        r = self._test_ping(node)
                        nodes_delay[node['add']] = r
                        print('use {} s'.format(str(r)))
                        f.write('node: {}\tdelay: {}\n'.format(node['add'], str(r)))
                print('done!\n')
            elif op == '3':
                pass
            else:
                print('input invalid!\n')


if __name__ == '__main__':
    sh = SubscribeHandler()
    sh.start()
