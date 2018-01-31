#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Input Data Format
# [lng, lat, gid, from/to, speed, direction]
# 
# Output data format
# 分方向分 Grid 聚集的结果
# [clusterID, lng, lat, gid, gLng, gLat, from/to, speed, direction]

import os
import numpy as np
from sklearn.cluster import DBSCAN
from util.tripFlow.base import parseFormatGID


class DBScanTFIntersections(object):
	def __init__(self, PROP):
		super(DBScanTFIntersections, self).__init__()
		# self.INPUT_PATH = os.path.join(PROP['IDIRECTORY'], 'bj-byhour-tf')
		self.OUTPUT_PATH = os.path.join(PROP['ODIRECTORY'], 'bj-byhour-res')
		self.directionNum = 4
		self.index = PROP['index']
		self.res = PROP['res']

		self.dbLabel = [[] for x in xrange(0, self.directionNum)]
		self.dbInput = [[] for x in xrange(0, self.directionNum)]
		self.subInfo = [[] for x in xrange(0, self.directionNum)]

		self.eps = PROP['eps']
		self.min_samples = PROP['min_samples']
		self.dbscanBaseNum = 0

	def run(self):
		self.iterateRes()
		noiseRate = self.dbscanProcess()
		ofilename = self.outputToFile()
		return noiseRate, ofilename
		
	def iterateRes(self):
		# 四个方向分别聚类
		for x in xrange(0, self.directionNum):
			currentDir = -1
			
			for line in self.res[x]:
				linelist = line.split(',')

				lng = float(linelist[0])
				lat = float(linelist[1])
				gid = int(linelist[2])
				gdirStr = linelist[3]
				speed = linelist[4]
				direction = linelist[5]
				gidInfo = parseFormatGID(gid, 'e')
				gLat = gidInfo['lat']
				gLng = gidInfo['lng']

				if currentDir == -1:
					currentDir = direction

				self.dbInput[x].append([lng, lat])
				subprops = "%s,%s,%s" % (gdirStr, speed, direction)
				self.subInfo[x].append([gid, gLng, gLat, subprops])

			print "Direction: %s - process completed. Total %d records." % (currentDir, len(self.res[x]))

	def dbscanProcess(self):
		# ######################
		# Compute DBSCAN
		# 
		noiseNum, totalNum = 0, 0

		for x in xrange(0, self.directionNum):
			X = self.dbInput[x]
			db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X)
			core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
			core_samples_mask[db.core_sample_indices_] = True
			labels = db.labels_

			index = 0
			totalNum += len(labels)
			while index < len(labels):
				if labels[index] != -1:
					labels[index] += self.dbscanBaseNum
				else:
					noiseNum += 1
				index += 1

			# print "PIDList [0]: %s, res [0]: %s" % (self.PIDList[x][0], res[0])

			# Number of clusters in labels, ignoring noise if present.
			n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
			self.dbscanBaseNum += n_clusters_
			self.dbLabel[x] = labels

			print "Direction No.%d, DS Cluster number: %d" % (x, n_clusters_)
		
		noiseRate = float(noiseNum)/totalNum
		print '''
===	Stats Info	===
Number of dbscan clusters in all:	%d
Records(has CID):	%d
Records(total):	%d
Noise Rate:	%f
===	Stats Info	===
''' % (self.dbscanBaseNum, noiseNum, totalNum, noiseRate)

		return noiseRate
	
	def outputToFile(self):
		"""
		通用输出文件函数
			:param self: 
			:param res: 
		"""
		
		# 待更新
		ores = []
		i = 0
		for i in xrange(0, self.directionNum):
			for j in xrange(0, len(self.dbLabel[i])):
				label = self.dbLabel[i][j]
				lngLatStr = "%.6f,%.6f" % (self.dbInput[i][j][0], self.dbInput[i][j][1])
				subInfoStr = "%d,%.6f,%.6f,%s" % (self.subInfo[i][j][0], self.subInfo[i][j][1], self.subInfo[i][j][2], self.subInfo[i][j][3])
				onerecStr = "%s,%s,%s" % (label, lngLatStr, subInfoStr)
				ores.append(onerecStr)

		ofilename = 'tfres-%d' % (self.index)
		ofile = os.path.join(self.OUTPUT_PATH, ofilename)
		with open(ofile, 'wb') as f:
			f.write('\n'.join(ores))
		f.close()

		return ofilename
		