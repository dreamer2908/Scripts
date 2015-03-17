#!/usr/bin/python
# encoding: utf-8

__module_name__ = "Check hash"
__module_author__ = "dreamer2908"
__module_version__ = "1.0"
__module_description__ = "Calculate checksums for DCC transfers"

import sys, os, math

try:
	import hexchat as xchat
except:
	import xchat as xchat

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

prevDccList = []
justCompleteList = []
plsContinue = True
checkHashHook = None

def hashFile(fileName, enableCRC32=True, enableMD5=True, enableSHA1=True, allCaps=False):
	import os, sys, hashlib, zlib

	crc32 = 0
	md5 = hashlib.md5()
	sha1 = hashlib.sha1()
	blockSize = 2 * 1024 * 1024

	try:
		fd = open(fileName, 'rb')
		while True:
			buffer = fd.read(blockSize)
			if len(buffer) == 0: # EOF or file empty. return hashes
				fd.close()
				if python2 and crc32 < 0:
					crc32 += 2 ** 32
				if allCaps:
					return '%08X' % crc32, md5.hexdigest().upper(), sha1.hexdigest().upper(), False
				else:					
					return '%08x' % crc32, md5.hexdigest(), sha1.hexdigest(), False
			if enableCRC32:
				crc32 = zlib.crc32(buffer, crc32)
			if enableMD5:
				md5.update(buffer)
			if enableSHA1:
				sha1.update(buffer)

	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		if allCaps:
			return '%08X' % 0, hashlib.md5().hexdigest().upper(), hashlib.sha1().hexdigest().upper(), error
		else:
			return '%08x' % 0, hashlib.md5().hexdigest(), hashlib.sha1().hexdigest(), error

def byteToHumanSize(size):
	if size >= 1000 * 1024 * 1024:
		return '%0.3f GiB' % (size / (2024 ** 3))
	elif size >= 1000 * 1024:
		return '%0.2f MiB' % (size / 1024 ** 2)
	elif size >= 1000:
		return '%0.1f KiB' % (size / 1024)
	else:
		return '%s bytes' % size

def checkHashHandler(word, word_eol, userdata):
	import os
	orgFname = word[0]
	destfile = word[1]
	if os.path.isfile(destfile):
		crc32, md5, sha1, error = hashFile(destfile, True, True, True, False)
		folder, fname = os.path.split(destfile)
		size = os.path.getsize(destfile)
		if not error:
			if fname == orgFname:
				xchat.prnt('Checksums for file \00320%s\017 (local, \00320%s\017): crc32 \00320%s\017, md5 \00320%s\017, sha1 \00320%s\017. Exact filesize: \00320%d\017 byte(s).' % (fname, byteToHumanSize(size), crc32.upper(), md5, sha1, size))
			else:
				xchat.prnt('Checksums for file \00320%s\017 (local, \00320%s\017, saved as \00320%s\017): crc32 \00320%s\017, md5 \00320%s\017, sha1 \00320%s\017. Exact filesize: \00320%d\017 byte(s).' % (orgFname, byteToHumanSize(size), fname, crc32.upper(), md5, sha1, size))
	return xchat.EAT_NONE

def controller(word, word_eol, userdata):
	global checkHashHook
	import os
	if len(word) > 1:
		if word[1] == 'stop':
			xchat.unhook(checkHashHook)
		elif word[1] == 'start':
			checkHashHook = xchat.hook_print("DCC RECV Complete", checkHashHandler)
		elif word[1] == 'file' and len(word) > 2:
			destfile = word[2]
			if os.path.isfile(destfile):
				crc32, md5, sha1, error = hashFile(destfile, True, True, True, False)
				folder, fname = os.path.split(destfile)
				size = os.path.getsize(destfile)
				if not error:
					xchat.prnt('Checksums for file \00320%s\017 (local, \00320%s\017): crc32 \00320%s\017, md5 \00320%s\017, sha1 \00320%s\017. Exact filesize: \00320%d\017 byte(s).' % (fname, byteToHumanSize(size), crc32.upper(), md5, sha1, size))
	return xchat.EAT_ALL

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

initStuff()
xchat.hook_command("checkhash", controller, help="Control Check hash")
checkHashHook = xchat.hook_print("DCC RECV Complete", checkHashHandler)
xchat.prnt(u'%s v%s plugin loaded' % (__module_name__, __module_version__))