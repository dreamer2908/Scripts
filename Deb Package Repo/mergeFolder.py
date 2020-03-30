#!/usr/bin/python
# encoding: utf-8

outDir = u'fonts'
moveMode = False

inputList = []
hashList = []

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
						pass
			else:
				try:
					shutil.move(sourceFile, targetFile)
				except:
					# failback: make a copy and delete the original
					try: 
						shutil.copy2(sourceFile, targetFile)
						os.unlink(sourceFile)
					except:
						pass

		hashList.append(sha256)

	elif move:
		try:
			os.unlink(sourceFile)
		except:
			try:
				os.unlink(sourceFile)
			except:
				pass

def moveFile(sourceFile, failbackFilename=None):
	copyFile(sourceFile, failbackFilename, True)

def initStuff():
	import sys
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
	global debug, inputList

	print('Processing %d input(s)...\n' % len(inputList))
	if debug:
		print(inputList)

	if not os.path.isdir(outDir):
		os.makedirs(outDir)

	for path in inputList:
		if os.path.isfile(path):
			copyFile(path, None)
		else:
			for (dirpath, dirnames, filenames) in os.walk(path):
				for fname in filenames:
					if not moveMode:
						copyFile(os.path.join(dirpath, fname), None)
					else:						
						moveFile(os.path.join(dirpath, fname), None)
		print('"%s" Done!' % path)

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
	# TODO: write it you lazyfag
	pass

parseParams()
checkSanity()
doStuff()