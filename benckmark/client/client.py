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

    @contextlib.contextmanager
    def start_iperf_server(self):
        proc = subprocess.Popen("iperf -s",shell=True,stdout=subprocess.PIPE, preexec_fn=os.setsid)
        try:
            yield
        finally:
            proc.terminate()
            proc.wait()
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError as e:
                logger.warn(e)

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
            logger.info("the runtimes_tags is {}".format(runtimes_tags))
            ##### 优先选择同一个网段，多次获取未果后，请求其他网段
            if runtimes_tags > 6 :
                SameRack = 'no'

            if runtimes_tags > 20 :
                value_list.append(-1)
                break

            server_host = ''
            send_iplist = []

            #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.connect((HOST, PORT))
            logger.info("{} : Will to send data to server ...".format(time()))
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
            logger.info("the data of get request what send to server is : {}".format(data))
            s.sendall(data)
            revdata = s.recv(1024)
            logger.info("revdata from server  is {}".format(revdata))
            ### 判断拿到的是不是一个IP，是就退出，否则继续
            p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
            ######## 连接的目标是自己的时候（使用了localserver）分发本机的IP
            if (p.match(revdata) and revdata not in connected_iplist) or netservertype == 'singlemode' :
                sleep(5)
                logger.info("will to run network benckmark ...")
                server_host = revdata
                transmit_time = 60
                connected_iplist.append(server_host)
                res = subprocess.Popen("iperf -c {} -t {} -y c".format(server_host,transmit_time),shell=True,close_fds=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                res.wait()
                res_stderr = res.stderr.read()
                res_stdout = res.stdout.read()
                if res_stderr and not res_stdout :
                    runtimes_tags += 1
                    logger.error("connted to iperf server faild !")
                    continue
                elif not res_stderr and res_stdout :
                    netdata = res_stdout
                    logger.info("the netdata is {}".format(netdata))
                try:
                    value = netdata.split(',')[-1]
                    value_list.append(value)
                    data = json.loads(data)
                    send_iplist.append(server_host)
                    send_iplist.append(self.myip)
                    
                    data['iplist'] = send_iplist
                    data['reqtype'] = "put"

                    data = json.dumps(data)
                    ##### 返回给 server 已经完成测试的 server_host IP，以便其他的机器测试
                    logger.info("the data of put request what send to server is : {}".format(data))
                    s.sendall(data)
                    success_runtimes -= 1
                    sleep(30)
                except:
                    logger.warn("the result of benckmark is illegal : {}".format(res.stdout.read()))
                    traceback.print_exc()
                    continue

            else:
                logger.info("continue ...")
                interval = random.randint(20,60)
                sleep_interval =  OnceTime + interval
                sleep(sleep_interval)

            logger.info("the iplist of had connected is : {}".format(connected_iplist))
            ### 记录循环运行的次数
            runtimes_tags += 1


        ### 求测试结果求多次中的最大值
        ### 判断三次测试是否全完成
        if success_runtimes == 0 :
            reslist = []
            reslist = [ int(i) for i in value_list ]
            netres = max(reslist)
        else :
            netres = -1

        data = {
            "iperf": "tag",
            "sertype": netservertype,
            "iplist": [],
            "status": ""
        }
        data['netres'] = netres
        data['status'] = "True"
        data['reqtype'] = "put"
        send_iplist.append(self.myip)
        data['iplist'] = send_iplist
        data = json.dumps(data)

        logger.info("the end data of put request what send to server is : {}".format(data))
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
            content = "network\t" + "network\t" + str(netres) + "\n"
            f.write(content)


class HandleData(object):

    def __init__(self, server, port, netservertype):
        self.server = server
        self.port = port
        self.netservertype = netservertype
        self.devicelist = ['cpu', 'memory', 'network', 'disk']
        #self.devicelist = ['memory','network']

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
            logger.info("run {} task".format(device))
            if device == 'network' :
                self.run_net_task()
            else:
                self.run_one_task(device)



    def readdata(self):
        self.run_all_task()
        sleep(3)
        alldevdict = {}

        rootdirpath = DataDir
        #### 获取结果数据的路径与之前定义的测试设备对应
        dirslist = self.devicelist 

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
                            except:
                                value = 0
                            devdict[devname] = value

                    #print "-=--= %s--=-=-=" % devdict
                    tmpdict[filename] = devdict
                    #print tmpdict

            alldevdict[dirname] = tmpdict

        #json_str = json.dumps(alldevdict)
        logger.info("the alldevdict is {}".format(alldevdict))
        return alldevdict


    def senddata(self, runtimes, token):
        global hadruntimes
        xbzy = hostinfo()
        ip = xbzy.gethostip()

        for i in range(0, runtimes):
            resdict =  self.readdata()
            resdict['ip'] = ip
            resdict['token'] = token
            sleep(30)
            ######## 建立连接，发送数据给服务端,发送运行次数
            hadruntimes = hadruntimes + 1
            logger.info("hadruntimes : {}".format(hadruntimes))
            resdict['hadruntimes'] = hadruntimes
            logger.info("data will send to server: {}".format(resdict))
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



def send_hart(pinstance, host, port, delay, token):
    global clien_id
    hdata = {}
    xbzy = hostinfo()
    hostip = xbzy.gethostip()
    #clien_id = hostip.replace('.', '-')
    clien_id = hostip
    hdata['ip'] = clien_id
    hdata['token'] = token
    hdata = json.dumps(hdata)
    logger.info("send heartbeat data: {}".format(hdata))

    while True:

        logger.info("client: {} report to server...".format(clien_id))
        if not pinstance.isAlive():
            logger.info("Heartbeat process done, will to exit")
            sys.exit(0)
        else:
            try:
                logger.info("{} send heartbeat data to server".format(clien_id))
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.sendall(hdata)
            except:
                logger.error("Heartbeat process cann't connect to server")
                sys.exit(-2)
        sleep(delay)


def main(argv):
    mode = ''
    server = ''
    token = ''
    netservertype = ''
    try:
        opts, args = getopt.getopt(argv,"hm:s:t:n",["mode=", "server=", "token=", "nettype"])
    except getopt.GetoptError:
        logger.info("-m < local/online > -s < server ip >")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logger.info("args : -m < local/online >  -s < server ip >  -t < token >")
            sys.exit(0)
        elif opt in ("-m", "--mode"):
            mode = arg

        elif opt in ("-s", "--server"):
            server = arg

        elif opt in ("-n", "--nettype"):
            netservertype = "singlemode"

        elif opt in ("-t", "--token"):
            token = arg

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
        hdata = HandleData(server, port, netservertype)
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
        logger.info("args : -m < local/online >  -s < server ip >  -t < token > -n")


if __name__ == '__main__':
    DataDir = '/tmp/delivery/data'
    Watcher()
    main(sys.argv[1:])
