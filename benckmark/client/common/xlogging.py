#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
 

class xlogger():
	

    def __init__(self, logfilepath):
        self.logfilepath = logfilepath

    def initlogger(self):
        # 获取logger实例，如果参数为空则返回root logger
        logger = logging.getLogger("AppName")
         
        # 指定logger输出格式
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
         
        # 文件日志
        #file_handler = logging.FileHandler("delivery_system.log")
        #file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式
        xloghandler = TimedRotatingFileHandler(self.logfilepath,
                                               when="d",
                                               interval=1,
                                               backupCount=7)
        xloghandler.setFormatter(formatter)
            
        logger.addHandler(xloghandler)
        
        
        # 控制台日志
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter  # 也可以直接给formatter赋值
         
        # 为logger添加的日志处理器
        #logger.addHandler(file_handler)
        logger.addHandler(xloghandler)
        logger.addHandler(console_handler)
         
        # 指定日志的最低输出级别，默认为WARN级别
        logger.setLevel(logging.INFO)
         
        # 输出不同级别的log
        #logger.debug('this is debug info')
        #logger.info('this is information')
        #logger.warn('this is warning message')
        #logger.error('this is error message')
        #logger.fatal('this is fatal message, it is same as logger.critical')
        #logger.critical('this is critical message')
         
        # 移除日志处理器
        #logger.removeHandler(file_handler)
        return logger
