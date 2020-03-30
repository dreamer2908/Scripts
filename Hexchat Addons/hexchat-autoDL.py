#!/usr/bin/python
# encoding: utf-8

# TODO: 
# - retry failed transfers
# - number of concurrent transfers
# - load/store download queue

__module_name__ = "Auto DL"
__module_author__ = "dreamer2908"
__module_version__ = "0.2"
__module_description__ = "Process XDCC transfers in queue"

import sys, os, math
from collections import deque

try:
	import hexchat as xchat
except:
	import xchat as xchat

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

transMax = 1
transCurrent = 0
transQueue = deque()
transHook = None
transHook2 = None

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

def transferStarter(word, word_eol, userdata):
	try:
		nextTransfer = transQueue.popleft()
		nick = nextTransfer[0]
		pack = str(nextTransfer[1])
		xchat.command('msg ' + nick + " xdcc send " + pack)
	except:
		pass
	return xchat.EAT_NONE

def startQueue():
	global transHook, transHook2
	transHook = xchat.hook_print("DCC RECV Complete", transferStarter)
	transHook2 = xchat.hook_print("DCC RECV Failed", transferStarter)

def stopQueue():
	global transHook, transHook2
	xchat.unhook(transHook)
	xchat.unhook(transHook2)
	transHook = None
	transHook2 = None

def controller(word, word_eol, userdata):
	global transHook, transHook2, transMax, transQueue
	import os
	if len(word) > 1:
		if word[1] == 'status':
			if transHook:
				xchat.prnt('Queue is active. Items in queue: %d' % len(transQueue))
			else:
				xchat.prnt('Queue is NOT active. Items in queue: %d' % len(transQueue))
		elif word[1] == 'stop':
			stopQueue()
			xchat.prnt('Queue deactivated. Note that active transfers haven\'t been cancelled.')
		elif word[1] == 'start':
			startQueue()
			if len(word) > 2 and word[2] == 'now':
				xchat.prnt('Queue activated. Starting transfers.')
				transferStarter(None, None, None)
			else:
				xchat.prnt('Queue activated. The next transfer will start when a current transfer ends. Run /autodl next to start one now.')
		elif word[1] == 'max' and len(word) > 2:
			transMax = word[2]
		elif word[1] == 'next':
			transferStarter(None, None, None)
		elif word[1] == 'remove':
			if word[2] == 'first':
				nextTransfer = transQueue.popleft()
			elif word[2] == 'last':
				nextTransfer = transQueue.pop()
			else:
				try:
					transID = int(word[2])
					nextTransfer = transQueue[transID]
					transQueue.remove(nextTransfer)
				except:
					pass
			try:
				nick = nextTransfer[0]
				pack = str(nextTransfer[1])
				xchat.prnt('Removed package #' + str(pack) + ' from nick ' + nick)
			except:
				xchat.prnt('None removed. Pls check your command.')
		elif word[1] == 'add' and len(word) > 3:
			nick = word[2]
			pack = word[3]
			transQueue.append((nick, pack))
			xchat.prnt('Added package #' + str(pack) + ' from nick ' + nick)
		elif word[1] == 'adds' and len(word) > 3:
			nick = word[2]
			for i in range(3, len(word)):
				pack = word[i]
				transQueue.append((nick, pack))
				xchat.prnt('Added package #' + str(pack) + ' from nick ' + nick)
		elif word[1] == 'batch' and len(word) > 4:
			nick = word[2]
			packStart = int(word[3])
			packEnd = int(word[4])
			for pack in range(packStart, packEnd + 1):
				transQueue.append((nick, pack))
				xchat.prnt('Added package #' + str(pack) + ' from nick ' + nick)
		elif word[1] == 'list':
			tmp = list(transQueue)
			xchat.prnt('Transfers in queue (%d):' % len(tmp))
			for item in tmp:
				xchat.prnt('  %s  %s' % (item[0], str(item[1])))
	return xchat.EAT_ALL

initStuff()
xchat.hook_command("autodl", controller, help="Control AutoDL")
xchat.prnt(u'%s v%s plugin loaded' % (__module_name__, __module_version__))