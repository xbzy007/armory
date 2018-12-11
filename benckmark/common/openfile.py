#!/usr/bin/env  python
# -*- coding: utf-8 -*-

import os, sys
import re, json
# print tag
alldevdict = {}

curdir = os.getcwd()
datadir = "data"
rootdirpath = curdir + '/' + datadir
dirslist = ['cpu', 'disk', 'memory']


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
            print filename
            filepath = dirpath + '/' + filename
            with open(filepath, 'r') as f:
                for line in f:
                    data = line.strip()
                    datalist = data.split()
                    devname = datalist[0]
                    value = datalist[-1]
                    devdict[devname] = value
                 
            print "-=--= %s--=-=-=" %devdict
            tmpdict[filename] = devdict
            print tmpdict

    alldevdict[dirname] = tmpdict

json_str = json.dumps(alldevdict)
print json_str
