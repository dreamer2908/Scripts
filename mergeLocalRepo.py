#!/usr/bin/python
# encoding: utf-8

# A random script written by dreamer2908 to do something not even remotely useful to you

import os, sys, time

outDir = u'/media/yumi/zZzZzZ/backup/LinuxMint/apt/tmp'
refDir = ["/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives1", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives2", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/dump", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/tmp"]
moveMode = False

inputList = ["/var/cache/apt/archives/"]
inputPrehashList = '/media/yumi/zZzZzZ/backup/LinuxMint/apt/prehash.txt'
hashList = []
prehashList = []
exploreInputRecursive = False

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False

debug = False

def fileAlreadyCopied(sHash):
	for h in hashList:
		if sHash == h:
			return True
	return False

def filePrehashed(fname):
	for entry in prehashList:
		name, sha256 = entry
		if fname == name:
			return sha256
	return False

def readInputPrehashList():
	import os, sys
	global inputPrehashList, prehashList
	f = open(inputPrehashList, 'r')
	fname = ''
	for l in f:
		if fname == '':
			fname = l[:-1] # kill the \n
		else:
			sha256 = l[:-1]
			prehashList.append((fname, sha256))
			fname = ''
	f.close()
	print('Imported %d entries from prehash input list.' % len(prehashList))

def hashFile(fileName):
	import os, sys, hashlib, zlib

	crc32 = 0
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
				return '%08X' % crc32, sha256.hexdigest().upper(), False
			crc32 = zlib.crc32(buffer, crc32)
			sha256.update(buffer)

	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		return '%08X' % 0, hashlib.sha256().hexdigest().upper(), error

def copyFile(sourceFile, failbackFilename=None, move=False):
	import shutil, os

	crc32, sha256, error = hashFile(sourceFile)
	if error:
		crc32, sha256, error = hashFile(sourceFile)
		if error:
			return

	if not fileAlreadyCopied(sha256):
		srcDir, srcName = os.path.split(sourceFile)
		targetFile = os.path.join(outDir, srcName)
		
		plsSkip = False
		error_v3 = False
		if os.path.isfile(targetFile):
			# check if the existing file is the same as the file we're processing			
			try:
				crc32_v2, sha256_v2, error_v2 = hashFile(sourceFile)
				if sha256 == sha256_v2:
					plsSkip = True
			except:
				try:
					crc32_v2, sha256_v2, error_v2 = hashFile(sourceFile)
					if sha256 == sha256_v2:
						plsSkip = True
				except:
					pass

			if failbackFilename == None:
				fileName, fileExtension = os.path.splitext(srcName)
				failbackFilename = fileName + ' [%s]' % crc32 + fileExtension
			targetFile = os.path.join(outDir, failbackFilename)

		if not plsSkip:
			
			if not move:
				try:
					shutil.copy2(sourceFile, targetFile)
				except:
					try:
						shutil.copy2(sourceFile, targetFile)
					except:
						error_v3 = True
			else:
				try:
					shutil.move(sourceFile, targetFile)
				except:
					# failback: make a copy and delete the original
					try: 
						shutil.copy2(sourceFile, targetFile)
						os.unlink(sourceFile)
					except:
						error_v3 = True

		hashList.append(sha256)
		if not error_v3:
			print('%s copied.' % srcName)
			return True

	elif move:
		try:
			os.unlink(sourceFile)
		except:
			try:
				os.unlink(sourceFile)
			except:
				pass
	return False

def moveFile(sourceFile, failbackFilename=None):
	return copyFile(sourceFile, failbackFilename, True)

def hashRefDir():
	import os, sys
	global refDir, hashList, prehashList

	print('Scanning reference dir(s)...')
	count = 0
	for dname in refDir:
		for (dirpath, dirnames, filenames) in os.walk(dname):
			for fname in filenames:
				if fname.endswith(".deb"):
					fullName = os.path.join(dirpath, fname)
					sha256 = filePrehashed(fullName)
					if sha256 == False:
						crc32, sha256, error = hashFile(fullName)
					hashList.append(sha256)
					count += 1
	print('Got %d files in %d reference dir(s). %d file(s) not in prehash list.' % (count, len(refDir), count - len(prehashList)))

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

def doStuff():
	import sys, os
	global debug, inputList, prehashList

	readInputPrehashList()

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
					if not moveMode:
						if copyFile(fullName, None):
							fileCopied += 1
							copiedSize += os.path.getsize(fullName)
					else:						
						if moveFile(fullName, None):
							fileCopied += 1
							copiedSize += os.path.getsize(fullName)
					fileProcessed += 1
				if not exploreInputRecursive: 
					break
		# print('"%s" Done!' % path)

	# get file count in outDir
	outDirFileCount = 0
	for (dirpath, dirnames, filenames) in os.walk(outDir):
		outDirFileCount = len(filenames)
		break

	print('\n%d file(s) scanned. %d new file(s), %s copied to output dir.' % (fileProcessed, fileCopied, byteToHumanSize(copiedSize)))
	print('Output dir now contains %d file(s).' % outDirFileCount)
	print('\nAll done.')

def parseParams():
	import sys, os
	global inputList, outDir, moveMode

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
			elif arg == 'move':
				moveMode = True
		else:
			inputList.append(arg)
		i += 1

	if len(inputList) > 0 and not os.path.isabs(outDir):
		parent, name = os.path.split(inputList[0])
		outDir = os.path.join(parent, outDir)

def checkSanity():
	global inputList
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

# Imported 3483 entries from prehash input list.
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