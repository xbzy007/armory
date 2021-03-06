#!/usr/bin/env python
# _*_  coding:utf8  _*_
# 2017-11-15@by xbzy007

import sys
import traceback
import random
import os
import getopt
import re
import subprocess
import threading
from time import ctime, sleep, time
import socket
import json
import signal
import contextlib
import argparse

sys.path.append("%s/common" % os.path.dirname(os.path.abspath(__file__)))
import xlogging

'''网络测试 运行三次求均值，没有完成运行的返回-1， 三次取最大值'''

xlogger = xlogging.xlogger('/tmp/delivery_server.log')
logger = xlogger.initlogger()


class ConnectMySQL(object):
    def __init__(self, DBHOST, DBPORT, DBUSER, DBPSSWD, DBNAME):
        self.dbhost = DBHOST
        self.dbport = DBPORT
        self.dbuser = DBUSER
        self.dbpasswd = DBPSSWD
        self.dbname = DBNAME

    def connectmysql(self):
        conn = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpasswd, db=self.dbname, charset="utf8")
        return conn

    def query(self, sqlstring):
        conn = self.connectmysql()
        cursor = conn.cursor()
        cursor.execute(sqlstring)
        returnData = cursor.fetchall()
        cursor.close()
        conn.close()
        return returnData


def createsoket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return s

class hostinfo(object):
    ## 获取本机的IP
    def gethostip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('223.5.5.5', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()

        return ip



class NetWork_Benchmark(object):

    def __init__(self):
        self.myip = self.gethostip()
    ######### 这里要确保已经安装了 iperf 
    #@contextlib.contextmanager
    def start_iperf_server(self):
        #proc = subprocess.Popen("iperf -s",shell=True,stdout=subprocess.PIPE, preexec_fn=os.setsid)
        proc = subprocess.Popen("iperf3 -s -4",shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
     #   try:
     #       yield
     #   finally:
     #       proc.terminate()
     #       proc.wait()
     #       try:
     #           os.killpg(proc.pid, signal.SIGTERM)
     #       except OSError as e:
     #           logger.warn(e)

    def gethostip(self):
        try:
            s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s1.connect(('223.5.5.5', 80))
            ip = s1.getsockname()[0]
        finally:
            s1.close()

        return ip


    def run_task(self,server, port, netservertype):

        OnceTime = 60
        connected_iplist = []

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server, port))
        except:
            logger.info("connecting server failed !")
            sys.exit(-1)

        success_runtimes = 3
        value_list = []
        runtimes_tags = 1
        while success_runtimes :
            revdata = ''
            SameRack = 'yes'
            logger.info("the runtimes_tags is {0}".format(runtimes_tags))
            ##### 优先选择同一个网段，多次获取未果后，请求其他网段
            if runtimes_tags > 6 :
                SameRack = 'no'

            if runtimes_tags > 50 :
                value_list.append(-1)
                break

            server_host = ''
            send_iplist = []

            #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.connect((HOST, PORT))
            logger.info("{0} : Will to send data to server ...".format(time()))
            data = {
                "iperf": "tag",
                "iplist": [],
                "status": 'False',
                "reqtype": "",
                "samerack": SameRack
            }
            data['reqtype'] = "get"
            data['sertype'] = netservertype
            data = json.dumps(data)
            logger.info("the data of get request what send to server is : {0}".format(data))
            s.sendall(data)
            revdata = s.recv(1024)
            logger.info("revdata from server  is {0}".format(revdata))
            ### 判断拿到的是不是一个IP，是就退出，否则继续
            p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
            ######## 连接的目标是自己的时候（使用了localserver）分发本机的IP
            if (p.match(revdata) and revdata not in connected_iplist) or netservertype == 'singlemode' :
                sleep(5)
                logger.info("will to run network benckmark ...")
                server_host = revdata
                transmit_time = 60
                connected_iplist.append(server_host)
                ########## 失败会中断？？？？？？
                try :
                    res = subprocess.Popen("iperf3 -c {0} -t {1} -J".format(server_host,transmit_time),close_fds=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE,shell=True)
                    res.wait()
                    res_stderr = res.stderr.read()
                    res_stdout = res.stdout.read()
                    logger.info("the res is {0},{1}".format(res_stderr,res_stdout))
                except :
                    pass

                if res_stderr and not res_stdout :
                    runtimes_tags += 1
                    logger.error("connted to iperf server faild !")
                    ######### 失败后也要归还资源
                    data = {
                        "iperf": "tag",
                        "iplist": [],
                        "status": 'False',
                        "reqtype": "",
                        "samerack": SameRack
                    }
                    send_iplist.append(server_host)
                    send_iplist.append(self.myip)
                    data['iplist'] = send_iplist
                    data['reqtype'] = "put"
                    data = json.dumps(data)
                    logger.error("network task failed, send to server is : {0}".format(data))
                    s.sendall(data)
                    sleep(5)
                    continue
                if not res_stderr and res_stdout :
                    netdata = res_stdout
                    logger.info("the netdata is {0}".format(netdata))
                try:
                    sum_sent = netdata['end']['sum_sent']['bits_per_second']
                    sum_received = netdata['end']['sum_received']['bits_per_second']
                    sum_sent_list.append(sum_sent)
                    sum_received_list.append(sum_sent)
                    data = json.loads(data)
                    send_iplist.append(server_host)
                    send_iplist.append(self.myip)
                    
                    data['iplist'] = send_iplist
                    data['reqtype'] = "put"

                    data = json.dumps(data)
                    ##### 返回给 server 已经完成测试的 server_host IP，以便其他的机器测试
                    logger.info("the data of put request what send to server is : {0}".format(data))
                    s.sendall(data)
                    success_runtimes -= 1
                    sleep(30)
                except:
                    logger.warn("the result of benckmark is illegal : {0}".format(res.stdout.read()))
                    traceback.print_exc()
                    continue

            else:
                logger.info("continue ...")
                interval = random.randint(20,60)
                sleep_interval =  OnceTime + interval
                sleep(sleep_interval)

            logger.info("the iplist of had connected is : {0}".format(connected_iplist))
            ### 记录循环运行的次数
            runtimes_tags += 1


        ### 求测试结果求多次中的最大值
        ### 判断三次测试是否全完成
        netres_dict = {}
        if success_runtimes == 0 :
            send_list = []
            recv_list = []
            send_list = [ int(i) for i in sum_send_list ]
            recv_list = [ int(i) for i in sum_received_list ]
            netres_send = max(send_list)
            netres_recv = max(recv_list)
            netres_dict['send_bw'] = netres_send
            netres_dict['recv_bw'] = netres_recv
        else :
            netres_dict['send_bw'] = -1
            netres_dict['recv_bw'] = -1
        send_iplist = []
        data = {
            "iperf": "tag",
            "sertype": netservertype,
            "iplist": [],
            "status": ""
        }
        data['netres_recv'] = netres_recv
        data['netres_send'] = netres_send
        data['status'] = "True"
        data['reqtype'] = "put"
        send_iplist.append(self.myip)
        data['iplist'] = send_iplist
        data = json.dumps(data)

        logger.info("the end data of put request what send to server is : {0}".format(data))
        s.sendall(data)
        s.close()
        #### 测试结果存入文件
        #filename = '/tmp/network_benchmark'
        netdatadir = DataDir + '/' +'network'
        if not os.path.exists(netdatadir): 
            os.makedirs(netdatadir)
        filename = 'bk_network_bw'
        filepath = netdatadir + '/' + filename
        with open(filepath, 'w') as f:
            for item, value in netres_dict.items():
                content = "{0}\t" + "network\t" + str({1}) + "\n".format(item, value)
                f.write(content)


class HandleData(object):

    def __init__(self, server, port, netservertype, device):
        self.server = server
        self.port = port
        self.netservertype = netservertype
        ############ "disk" 作为参数会传到执行脚本， 测试生成disk_bw,disk_iops
        self.devicelist = device

    def run_one_task(self, devicename):
        currentdir = os.path.dirname(os.path.realpath(__file__))
        # output = os.popen('cd %s && bash SysBenchmark.sh' % currentdir)
        # returnCode = subprocess.call("ls -lh",shell=True)
        # returnCode = subprocess.call("cd %s && bash SysBenchmark.sh" %currentdir,shell=True)
        ### cpu benchmark
        p = subprocess.Popen("cd %s && bash SysBenchmark.sh %s" %(currentdir, devicename), shell=True, stdout=subprocess.PIPE,\
                             stderr=subprocess.STDOUT)
        p.wait()

        rescode = p.returncode
        return  rescode

    def run_net_task(self):
        ### network benchmark
        xnet = NetWork_Benchmark()
        xnet.run_task(self.server, self.port, self.netservertype)

    def run_all_task(self):
        for device in self.devicelist :
            logger.info("run {0} task".format(device))
            if device == 'network' :
                try:
                    self.run_net_task()
                except:
                    logger.error("run {0} task failed, function comtinue".format(device))
                    continue
            else:
                try:
                    self.run_one_task(device)
                except:
                    continue



    def readdata(self):
        ### run benckmark task
        self.run_all_task()
        sleep(3)
        alldevdict = {}

        rootdirpath = DataDir
        #### 定义数据的目录列表, 这里可以直接获取data 下的所有目录名字
        dirslist = ['cpu', 'memory', 'network', 'disk_bw', 'disk_iops']

        def file_name(dirpath):
            files = []
            for root, dirs, files in os.walk(dirpath):
                pass
            return files

        for dirname in dirslist:
            dirpath = rootdirpath + '/' + dirname
            Files = file_name(dirpath)
            #    print  "dirpath: %s: %s" %(dirpath,Files)
            tmpdict = {}
            for filename in Files:
                if re.match('bk', filename):
                    devdict = {}
                    #print filename
                    filepath = dirpath + '/' + filename
                    with open(filepath, 'r') as f:
                        for line in f:
                            data = line.strip()
                            datalist = data.split()
                            devname = datalist[0]
                            value = datalist[-1]
                            ###  判断 value 是否为数字
                            try:
                                value = float(value)
                                value = round(value,2)
                            except:
                                value = 0
                            devdict[devname] = value

                    #print "-=--= %s--=-=-=" % devdict
                    tmpdict[filename] = devdict
                    #print tmpdict

            alldevdict[dirname] = tmpdict

        #json_str = json.dumps(alldevdict)
        logger.info("the alldevdict is {0}".format(alldevdict))
        return alldevdict


    def senddata(self, runtimes, token):
        global hadruntimes
        xbzy = hostinfo()
        ip = xbzy.gethostip()
        ### 探测服务端连接，连接不可用，退出线程
        try:
            ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ds.connect((self.server, self.port))
            sleep(1)
        except:
            logger.error("connecting to server failed!, cann't continue")
            sys.exit(-1)

        for i in range(0, runtimes):
            resdict =  self.readdata()
            resdict['ip'] = ip
            resdict['token'] = token
            sleep(30)
            ######## 建立连接，发送数据给服务端,发送运行次数
            hadruntimes = hadruntimes + 1
            logger.info("hadruntimes : {0}".format(hadruntimes))
            resdict['hadruntimes'] = hadruntimes
            logger.info("data will send to server: {0}".format(resdict))
            data = json.dumps(resdict)
            ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                ds.connect((self.server, self.port))
                ds.sendall(data)
                sleep(10)
            except:
                logger.error("connecting to server failed!, cann't send data")
                sleep(5)

class Watcher():

    def __init__(self):
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError:
            pass



def send_hart(process_object,host, port, delay, token):
    global clien_id
    hdata = {}
    xbzy = hostinfo()
    hostip = xbzy.gethostip()
    #clien_id = hostip.replace('.', '-')
    clien_id = hostip
    hdata['ip'] = clien_id
    hdata['token'] = token
    hdata = json.dumps(hdata)
    logger.info("send heartbeat data: {0}".format(hdata))
    check_tag = 0
    while True:
        logger.info("client: {0} report to server...".format(clien_id))
        if not process_object.isAlive():
            check_tag += 1
        if check_tag > 3 :
            logger.info("main process exit, heartbeat will to exit")
            sys.exit(0)
        try:
            logger.info("{0} send heartbeat data to server".format(clien_id))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.sendall(hdata)
        except:
            logger.error("Heartbeat process cann't connect to server")
            sys.exit(-2)
        sleep(delay)


def main():
    mode = ''
    server = ''
    token = ''
    device = []
    netservertype = ''
    args = argparse.ArgumentParser(description = 'Help Information ',epilog = 'Information end ')
    args.add_argument("-m","--mode", type = str, dest = 'mode',  help = "run mode: local/online",required = True)
    args.add_argument("-s","--server", type = str, dest = 'server',  help = "server address",required = True)
    args.add_argument("-t","--token", type = str, dest = 'token',  help = "token",required = True)
    args.add_argument('-n', action='store_const', dest='netservertype',const=True, help='set network benckmark type')
    args.add_argument("-d","--device", type = str, dest = 'device', help = "device name", required = False, default = ['cpu', 'memory', 'network', 'disk'], nargs = '*')

    args = args.parse_args()
    print "argparse.args=",args,type(args)
    mode = args.mode
    server = args.server
    token = args.token
    device = args.device
    netservertype = args.netservertype

    global hadruntimes

    hadruntimes = 0
    port = 8818
    hport = 8819
    runtimes = 1  # 默认跑一次，目前暂时支持一次
    clien_id = 0  # 客户端注册id
    threads = []
    ht_interval = 10

    global TData

    if not netservertype :
        netservertype = 'peer'

    if mode in ['online', 'local'] :
        hdata = HandleData(server, port, netservertype, device)
        if mode == 'online' :
            if not server or not token:
                logger.warn("need : -s < server ip > -t < token >")
                sys.exit(3)

            #函数名字已经改变 重新写如下代码
            xiperf = NetWork_Benchmark()
            iperf_server = threading.Thread(target=xiperf.start_iperf_server,args=())
            threads.append(iperf_server)

            TData = threading.Thread(target=hdata.senddata, args=(runtimes, token))
            #print type(TData)
            threads.append(TData)
            THeartbeat = threading.Thread(target=send_hart, args=(TData, server, hport, ht_interval, token))
            threads.append(THeartbeat)

        elif mode == 'local' :
            TData = threading.Thread(target=hdata.readdata)
            threads.append(TData)
        for t in threads:
            t.setDaemon(True)
            t.start()
        t.join()
        logger.info("all process done")

    else:
        helpinfo()


if __name__ == '__main__':
    DataDir = '/tmp/delivery/data'
    Watcher()
    main()
