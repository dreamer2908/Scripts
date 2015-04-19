#!/usr/bin/python
# encoding: utf-8

# A random script written by dreamer2908 to do something not even remotely useful to you
# TODO: re-write into a full-feature local repo maker
# - DB stores package info, including output of `dpkg-deb --info x.deb`, size, md5, sha1, sha256 checksums [done]
# - Write Packages automatically. gz is optional [done]
# - Clean up old versions (to Dump) automatically
# - Maybe intergrate local_package_update functions
# TL;DR: eliminate the nedd of mergeTmp; this script alone should be enough

import os, sys, time, subprocess

outDir = u'/media/yumi/zZzZzZ/backup/LinuxMint/apt/tmp'
refDir = ["/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives1", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives2", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/dump", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/tmp"]
dumpDir = "/media/yumi/zZzZzZ/backup/LinuxMint/apt/dump"
target1 = '/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives1'
target2 = '/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives2'

inputList = ["/var/cache/apt/archives/"]
exploreInputRecursive = False

dbFile = '/media/yumi/zZzZzZ/backup/LinuxMint/apt/pkgInfo.csv'
hashDB = dict() 
hashDict = dict()
hashDictDup = dict()

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

def byteToHumanSize(size):
	if size >= 1000 * 1024 * 1024:
		return '%0.3f GiB' % (size / (1024 ** 3))
	elif size >= 1000 * 1024:
		return '%0.3f MiB' % (size / 1024 ** 2)
	elif size >= 1000:
		return '%0.3f KiB' % (size / 1024)
	elif size >= 2:
		return '%s bytes' % size
	else:
		return '%s byte' % size

def fileAlreadyCopied(sHash):
	return sHash in hashDict

def getFileSize(fileName):
	if os.path.isfile(fileName):
		return os.path.getsize(fileName)
	else:
		print('File not found: %s' % fileName)
		return -1

def hashFile(fileName):
	import os, sys, hashlib, zlib

	crc32 = 0
	md5 = hashlib.md5()
	sha1 = hashlib.sha1()
	sha256 = hashlib.sha256()
	blockSize = 2 * 1024 * 1024

	try:
		fd = open(fileName, 'rb')
		while True:
			buffer = fd.read(blockSize)
			if len(buffer) == 0: # EOF or file empty. return hashes
				fd.close()
				if python2 and crc32 < 0:
					crc32 += 2 ** 32
				return '%08X' % crc32, md5.hexdigest().upper(), sha1.hexdigest().upper(), sha256.hexdigest().upper(), False
			crc32 = zlib.crc32(buffer, crc32)
			md5.update(buffer)
			sha1.update(buffer)
			sha256.update(buffer)

	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		return '%08X' % 0, hashlib.md5().hexdigest().upper(), hashlib.sha1().hexdigest().upper(), hashlib.sha256().hexdigest().upper(), error

def copyFile(sourceFile, failbackFilename=None):
	import shutil, os

	crc32, md5, sha1, sha256, error = hashFile(sourceFile)
	if error:
		crc32, md5, sha1, sha256, error = hashFile(sourceFile)
		if error:
			return

	if not fileAlreadyCopied(sha256):
		srcDir, srcName = os.path.split(sourceFile)
		targetFile = os.path.join(outDir, srcName)
		
		plsSkip = False
		error = False
		if os.path.isfile(targetFile):					
			try: # check if the existing file is the same as the file we're processing	
				crc32_v2, md5_v2, sha1_v2, sha256_v2, error_v2 = hashFile(targetFile)
				if sha256 == sha256_v2:
					plsSkip = True
			except:
				pass

			if not failbackFilename:
				fileName, fileExtension = os.path.splitext(srcName)
				failbackFilename = fileName + ' [%s]' % crc32 + fileExtension
			targetFile = os.path.join(outDir, failbackFilename)

		if not plsSkip:
			try:
				shutil.copy2(sourceFile, targetFile)
			except:
				error = True

		if not error:		
			fileSize = getFileSize(sourceFile)
			debInfo = getDebInfo(sourceFile)
			hashDict[sha256] = (targetFile, crc32, md5, sha1, fileSize, debInfo)
			print('%s copied.' % srcName)
			return True

	return False

# executes given task and return console output, return code and error message if any
def executeTask(params):
	import subprocess, sys

	execOutput = ''
	returnCode = 0
	error = False
	try:
		execOutput = subprocess.check_output(params)
	except subprocess.CalledProcessError as e:
		execOutput = e.output
		returnCode = e.returncode
		error = True
	if sys.stdout.encoding: # It's None when debugging in Sublime Text
		execOutput = execOutput.decode(sys.stdout.encoding)

	return execOutput, returnCode, error

def getDebInfo(fname):
	params = ['dpkg-deb', '--info', '%s' % fname]
	execOutput, returnCode, error = executeTask(params)
	infos = execOutput.split('\n')

	for i in range(len(infos)):
		infos[i] = infos[i][1:]

	for i in range(len(infos)):
		if infos[i].startswith('Package: '):
			return '\n'.join(infos[i:])
	return ''

def hashRefDir():
	import csv

	if os.path.isfile(dbFile):
		f = open(dbFile, 'r', newline='\n') # newline only available in Python 3
		reader = csv.reader(f)
		for row in reader:
			fname = row[0]
			crc32 = row[1]
			md5 = row[2]
			sha1 = row[3]
			sha256 = row[4]
			try:
				size = row[5]
			except:
				size = -1
			try:
				debInfo = row[6]
			except:
				debInfo = ''
			hashDB[fname] = (crc32, md5, sha1, sha256, size, debInfo)
		f.close()

	print('Imported %d entries from database.' % len(hashDB))

	print('Scanning reference dir(s)...')
	count = 0
	for dname in refDir:
		for (dirpath, dirnames, filenames) in os.walk(dname):
			for fname in filenames:
				if fname.endswith(".deb"):
					fullName = os.path.join(dirpath, fname)
					crc32, md5, sha1, sha256, size, debInfo = (None, None, None, None, None, None) # I forgot that vars aren't disposed that quickly
					if fullName in hashDB:
						crc32, md5, sha1, sha256, size, debInfo = hashDB[fullName]
					else:
						crc32, md5, sha1, sha256, error = hashFile(fullName)
					if size == None or size == -1 or size == '-1' or size == '': # it can be a string
						size = str(getFileSize(fullName))
					if not debInfo:
						debInfo = getDebInfo(fullName)
					if sha256 not in hashDict:
						hashDict[sha256] = [fullName, crc32, md5, sha1, size, debInfo]
					else:
						hashDictDup[fullName] = [crc32, md5, sha1, sha256, size, debInfo]
					count += 1

	print('Got %d files in %d reference dir(s). %d file(s) not in database.' % (count, len(refDir), max(0, count - len(hashDB))))

def saveHashDB():
	import csv

	# write out the 'database'
	f = open(dbFile, 'w', newline='\n') # newline only available in Python 3
	writer = csv.writer(f)

	for sha256 in hashDict:
		fname, crc32, md5, sha1, size, debInfo = hashDict[sha256]
		row = (fname, crc32, md5, sha1, sha256, size, debInfo)
		writer.writerow(row)

	for fname in hashDictDup:
		row = tuple([fname] + list(hashDictDup[fname]))
		writer.writerow(row)

	f.close()


def getInfoFromPkg(debInfo, infoType):
	infos = debInfo.split('\n')
	for i in infos:
		if i.startswith(infoType):
			return i.split(' ')[1]

def sortPkg():
	# put amd64 and all packages in archives1, i386 ones in archives2, old and repeat ones in dump
	# after this, temp should either be empty or contain one random package
	# hashDictDup should be empty (OK, it's fine even if it's not empty), and hashDict contains only latest versions
	# hashDict* must be in sync with files
	global hashDict, hashDictDup

	import apt_pkg, shutil
	apt_pkg.init()

	def comparePkg(pkgName, pkgInfo):
		if pkgName in pkgDict:
			# check arch, version, location, etc.
			arch1 = getInfoFromPkg(pkgInfo[6], 'Architecture:')
			arch2 = getInfoFromPkg(pkgDict[pkgName][6], 'Architecture:')
			if arch1 != arch2:
				pkgDictMore.append(pkgInfo)
				return

			# replace if same arch, later version, in archives1 or archives 2 and existing one in tmp or dump
			replaceIt = False
			v1 = getInfoFromPkg(pkgInfo[6], 'Version:')
			v2 = getInfoFromPkg(pkgDict[pkgName][6], 'Version:')
			path1 = os.path.split(pkgInfo[0])[0]
			path2 = os.path.split(pkgDict[pkgName][0])[0]
			if apt_pkg.version_compare(v1, v2) > 0:
				replaceIt = True
			elif apt_pkg.version_compare(v1, v2) == 0:
				if (path2.endswith('tmp') or path2.endswith('dump')) and (path1.endswith('archives1') or path1.endswith('archives2')):
					replaceIt = True
			if replaceIt:
				# TODO: dump 2
				src = pkgDict[pkgName][0]
				dst = dumpDir
				try:
					os.unlink(src)
				# 	shutil.move(src, dst)
				# 	pkgDict[pkgName][0] = os.path.join(dst, os.path.split(src)[1])
				# 	# print('Dumping 2: moving %s...' % (src))
				# 	# print('v1 = %s, v2 = %s, path1 = %s, path2 = %s' % (v1, v2, path1, path2))
				except:
				# 	pkgDict[pkgName][0] = src
					pass
				# pkgDictDup.append(pkgDict[pkgName])

				if (path1.endswith('tmp') or path1.endswith('dump')):
					src = pkgDict[pkgName][0]
					if arch1 == 'all' or arch1 == 'amd64':
						dst = target1
					else:
						dst = target2
				try:
					shutil.move(src, dst)
					pkgInfo[0] = os.path.join(dst, os.path.split(src)[1])
				except:
					pkgInfo[0] = src
				pkgDict[pkgName] = pkgInfo
			else:
				# TODO: dump 1
				src = pkgInfo[0]
				dst = dumpDir
				try:
					os.unlink(src)
				# 	shutil.move(src, dst)
				# 	pkgInfo[0] = os.path.join(dst, os.path.split(src)[1])
				# 	# print('Dumping 1: moving %s...' % (src))
				# 	# print('v1 = %s, v2 = %s, path1 = %s, path2 = %s' % (v1, v2, path1, path2))
				except:
				# 	pkgInfo[0] = src
					pass
				# pkgDictDup.append(pkgInfo)
		else:
			pkgDict[pkgName] = pkgInfo

	pkgDict = dict()
	pkgDictMore = []
	pkgDictDup = []

	for sha256 in hashDict:
		fname, crc32, md5, sha1, size, debInfo = hashDict[sha256]
		pkgName = getInfoFromPkg(debInfo, 'Package:')
		pkgInfo = [fname, crc32, md5, sha1, sha256, size, debInfo]
		comparePkg(pkgName, pkgInfo)

	for fname in hashDictDup:
		crc32, md5, sha1, sha256, size, debInfo = hashDictDup[fname]
		pkgName = debInfo.split('\n')[0].split(' ')[1]
		pkgInfo = [fname, crc32, md5, sha1, sha256, size, debInfo]
		comparePkg(pkgName, pkgInfo)

	# write hashDict
	hashDict = dict()
	hashDictDup = dict()
	for pkgName in pkgDict:
		fname, crc32, md5, sha1, sha256, size, debInfo = pkgDict[pkgName]
		hashDict[sha256] = [fname, crc32, md5, sha1, size, debInfo]
	for pkgInfo in pkgDictMore:
		fname, crc32, md5, sha1, sha256, size, debInfo = pkgInfo
		hashDict[sha256] = [fname, crc32, md5, sha1, size, debInfo]
	for pkgInfo in pkgDictMore:
		fname, crc32, md5, sha1, sha256, size, debInfo = pkgInfo
		hashDictDup[fname] = [crc32, md5, sha1, sha256, size, debInfo]

def writePackages():
	# delete existing Package and Package.gz in each dir in refDir
	# make a dict with dir in refDir as key, value is a list of package infos of packages in that dir
	# sort and write out them

	# delete files
	deleteMe = ('Packages', 'Packages.gz', 'Packages.bz2')
	for dname in refDir:
		for fname in deleteMe:
			try:
				os.unlink(os.path.join(dname, fname))
			except:
				pass # might do something later

	# sort packages
	outPkgs = dict()
	for sha256 in hashDict:
		fullname, crc32, md5, sha1, size, debInfo = hashDict[sha256]
		dname, fname = os.path.split(fullname)
		pkgInfo = [fname, crc32, md5, sha1, sha256, size, debInfo]
		if dname not in outPkgs:
			outPkgs[dname] = []
		outPkgs[dname].append(pkgInfo)

	for fullname in hashDictDup:
		dname, fname = os.path.split(fullname)
		pkgInfo = list([os.path.split(fullname)[1]] + list(hashDictDup[fullname]))
		if dname not in outPkgs:
			outPkgs[dname] = []
		outPkgs[dname].append(pkgInfo)

	for dname in refDir: # make sure all dirs in refDir have Packages, even if empty
		if dname not in outPkgs:
			outPkgs[dname] = []

	# write Packages
	for dname in outPkgs:
		outFname = os.path.join(dname, 'Packages')
		writer = open(outFname, 'w', newline='\n')
		for pkgInfo in outPkgs[dname]:
			fname, crc32, md5, sha1, sha256, size, debInfo = pkgInfo
			debInfo = debInfo.strip()

			str2wr = debInfo + '\nFilename: ./' + fname + '\nSize: ' + str(size) + '\nMD5sum: ' + md5.lower() + '\nSHA1: ' + sha1.lower() + '\nSHA256: ' + sha256.lower() + '\n\n'
			writer.write(str2wr)

		writer.write('\n')
		writer.close()

def doStuff():
	hashRefDir()

	print('\nScanning input dir(s)...')

	if not os.path.isdir(outDir):
		os.makedirs(outDir)

	fileProcessed = 0
	fileCopied = 0
	copiedSize = 0
	for path in inputList:
		if os.path.isfile(path):
			copyFile(path, None)
		else:
			for (dirpath, dirnames, filenames) in os.walk(path):
				for fname in filenames:
					fullName = os.path.join(dirpath, fname)
					if copyFile(fullName, None):
						fileCopied += 1
						copiedSize += os.path.getsize(fullName)
					fileProcessed += 1
				if not exploreInputRecursive: 
					break

	print('\nCleaning up packages...')
	sortPkg()

	print('\nSaving database...')
	saveHashDB()

	print('\nWriting packages info...')
	writePackages()

	# get file count in outDir
	outDirFileCount = 0
	for (dirpath, dirnames, filenames) in os.walk(outDir):
		for fname in filenames:
			if fname.endswith('.deb'):
				outDirFileCount += 1
		break

	print('\n%d file(s) scanned. %d new file(s), %s copied to output dir.' % (fileProcessed, fileCopied, byteToHumanSize(copiedSize)))
	print('Output dir now contains %d deb file(s).' % outDirFileCount)
	print('\nAll done.')

def initStuff():
	import sys, time
	global defaultTimer, terminalSupportUnicode, python2, win32

	# Stats setup
	if sys.platform == 'win32':
		# On Windows, the best timer is time.clock
		defaultTimer = time.clock
		win32 = True
	else:
		# On most other platforms the best timer is time.time
		defaultTimer = time.time
		win32 = False

	terminalSupportUnicode = True
	try:
		text = u'「いなり、こんこん、恋いろは。」番宣ＰＶ'.encode(sys.stdout.encoding)
	except:
		terminalSupportUnicode = False

	if sys.version_info[0] < 3:
		python2 = True

def parseParams():
	import sys, os
	global inputList, outDir

	i = 1
	while i < len(sys.argv):
		arg = sys.argv[i]
		if arg.startswith('-'):
			if arg.startswith('--'):
				arg = arg[2:]
			else:
				arg = arg[1:]
			arg = arg.lower()
			if arg == 'outdir' and i < len(sys.argv) - 1:
				outDir = sys.argv[i+1]
		else:
			inputList.append(arg)
		i += 1

	if len(inputList) > 0 and not os.path.isabs(outDir):
		parent, name = os.path.split(inputList[0])
		outDir = os.path.join(parent, outDir)

def checkSanity():
	import sys
	if len(inputList) < 1:
		printReadMe()
		sys.exit(1)

def printReadMe():
	# Just a placeholder in my usual templete
	pass

initStuff()
# parseParams()
# checkSanity()
doStuff()

# OUTPUT SHOULD LOOK LIKE THIS:

# Imported 3483 entries from database.
# Scanning reference dir(s)...
# Got 3500 files in 4 reference dir(s).

# Scanning input dir(s)...
# python3.4-dev_3.4.0-2ubuntu1_amd64.deb copied.
# cython_0.20.1+git90-g0e6e38e-1ubuntu2_amd64.deb copied.
# python2.7-dev_2.7.6-8_amd64.deb copied.
# python3-dev_3.4.0-0ubuntu2_amd64.deb copied.
# python-dev_2.7.5-5ubuntu3_amd64.deb copied.
# mpv_2%3a0.5.0+git~ppa_amd64.deb copied.
# libpython3.4-dev_3.4.0-2ubuntu1_amd64.deb copied.
# libpython3-dev_3.4.0-0ubuntu2_amd64.deb copied.
# cython3_0.20.1+git90-g0e6e38e-1ubuntu2_amd64.deb copied.

# 173 file(s) scanned. 9 new file(s) copied to output dir.
# All done.
# [Finished in 7.5s]