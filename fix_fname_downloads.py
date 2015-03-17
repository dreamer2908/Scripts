#!/usr/bin/python3
# encoding: utf-8

# Quick & dirty. Caused an accident at first try.

import os, sys, time, shutil
try:
	from urllib2 import unquote
except:
	from urllib.parse import unquote

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

inputList = []
exploreInputRecursive = True
dryRun = False

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

def fixFname(fullname):
	import sys, os, shutil

	dirname, fname = os.path.split(fullname)
	newFname = unquote(fname)

	char1 = u'<>:"/\\|?*\n\r'
	char2 = u'＜＞：＂／＼｜？＊  '
	for i in range(len(char1)):
		newFname = newFname.replace(char1[i], char2[i])

	newFname = newFname.strip()

	if (newFname.endswith(".mkv") or newFname.endswith(".mkv.part")) and not newFname.startswith("[UTW]") and not newFname.startswith("[Watashi]"): # here we go millions of exceptions
		newFname = newFname.replace('_', ' ')

	if (newFname.endswith(".mp4") or newFname.endswith(".flv") or newFname.endswith(".webm")) and newFname.startswith("_"): # fixed the hack
		newFname = newFname.strip("_")

	if newFname != fname:
		print('Attempting to rename the file "%s" into "%s" (in directory %s)' % (fname, newFname, dirname))
		if not dryRun:
			try:
				shutil.move(fullname, os.path.join(dirname, newFname))
			except Exception as e:
				print(e)
				return fullname
	return os.path.join(dirname, newFname)

def doStuff():
	import sys, os, time

	fileProcessed = 0
	for path in inputList:
		if os.path.isfile(path):
			fixFname(path)
			fileProcessed += 1
		else:
			for (dirpath, dirnames, filenames) in os.walk(path):
				dirpath = fixFname(dirpath)
				for fname in filenames:
					fixFname(os.path.join(dirpath, fname))
					fileProcessed += 1
				if not exploreInputRecursive:
					break

def parseParams():
	global inputList
	i = 1
	while i < len(sys.argv):
		arg = sys.argv[i]
		if arg.startswith('-'):
			pass
		else:
			inputList.append(arg)
		i += 1

def checkSanity():
	import sys

	sane = True
	if not sane:
		printReadMe()
		sys.exit()

def printReadMe():
	pass

initStuff()
parseParams()
checkSanity()
doStuff()