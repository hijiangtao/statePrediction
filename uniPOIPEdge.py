#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

import sys
import time
import logging
import getopt
from multiprocessing import Process
from util.UniPOIEdgeBasic import UniPOIEdgeBasic
from util.dbopts import connectMongo


def processTask(x, city, directory, inum, poiMap, subopath): 
	PROP = {
		'INDEX': x, 
		'CITY': city, 
		'DIRECTORY': directory, 
		'INUM': inum,
		'poiMap': poiMap,
		'SUBOPATH': subopath
	}

	task = UniPOIEdgeBasic(PROP)
	task.run()


def usage():
	"""
	使用说明函数
	"""
	print '''Usage Guidance
help	-h	get usage guidance
city	-c	city or region name, such as beijing
directory	-d	the root directory of records and results, such as /China/beijing
inum	-i	number of input files
onum	-o	number of output files
'''


def main(argv):
	"""
	主入口函数
		:param argv: city 表示城市， directory 表示路径， inum 表示输入文件总数， onum 表示输出文件总数， jnum 表示处理进程数，通常和 onum 一致， subopath 为结果存储的子目录名字
	"""
	try:
		opts, args = getopt.getopt(argv, "hc:d:i:j:", ["help", "city=", 'directory=', 'inum=', 'jnum='])
	except getopt.GetoptError as err:
		print str(err)
		usage()
		sys.exit(2)

	city, directory, inum, jnum, subopath = 'beijing', '/home/tao.jiang/datasets/JingJinJi/records', 86, 20, 'bj-newvis-sg'
	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-c", "--city"):
			city = arg
		elif opt in ("-d", "--directory"):
			directory = arg
		elif opt in ('-i', '--inum'):
			inum = int(arg)
		elif opt in ('-j', '--jnum'):
			jnum = int(arg)

	STARTTIME = time.time()
	print "Start approach at %s" % STARTTIME

	# 固定网格总数
	poiMap = {}
	conn, db = connectMongo('stvis')
	plist = list(db['grids'].find({}, {
		'pid': 1,
		'nid': 1
	}))
	conn.close()
	
	print "POI List length: %d" % len(plist)
	for each in plist:
		poiMap[each['nid']] = each['pid']
	# plist = None

	# @多进程运行程序 START
	jobs = []

	for x in xrange(0, jnum):
		jobs.append(Process(target=processTask, args=(x, city, directory, inum, poiMap, subopath)))
		jobs[x].start()

	for job in jobs:
		job.join()

	# 文件过于庞大，故不做合并处理
	# mergeMultiProcessMatFiles(directory, subopath, jnum)

	# @多进程运行程序 END

	print "END TIME: %s" % time.time()


if __name__ == '__main__':
	logging.basicConfig(filename='logger-unippoiedge.log', level=logging.DEBUG)
	main(sys.argv[1:])