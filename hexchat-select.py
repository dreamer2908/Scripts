#!/usr/bin/python
# encoding: utf-8

__module_name__ = "Select"
__module_author__ = "dreamer2908"
__module_version__ = "1.0"
__module_description__ = "!select inside outside"

import sys, os, math, random

try:
	import hexchat as xchat
except:
	import xchat as xchat

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

hookList = []
delayHook = None
eventList1 = ["Channel Message", "Channel Msg Hilight"]	# If someone HLs you, it's Channel Msg Hilight, not Channel Message
eventList2 = ["Notice"]
eventList3 = ["Private Message", "Private Message To Dialog"]
eventList4 = ["Your Message"]

inProgress = False

def delayExecute(command, time):
	global delayHook
	delayHook = xchat.hook_timer(time, delayExecuteSub, command)

def delayExecuteSub(command):
	global delayHook
	xchat.command(command)
	xchat.unhook(delayHook)

def selectMain(word, word_eol, userdata):
	# solution to recursive events when capturing Your Message event
	global inProgress
	if inProgress:
		return
	inProgress = True
	# userdata 1. channel message 2. notice 3. private msg 4. your message
	# Event Channel Message, Channel Msg Hilight, Private Message all have [0] nickname, [1] the message
	try:
		text = xchat.strip(word[1]).strip()
		if text.startswith('!select '):
			selection = selectSub(word[1])
			if userdata == 1 and selection != None:
				delayExecute('say %s' % selection, 1) # use delay execution to fix disordered message <me>inside  <me>!select inside outside
			elif userdata == 2 and selection != None:
				delayExecute('notice %s %s' % (word[0], selection), 1)
			elif userdata == 3 and selection != None: # delay length doesn't matter; even 1ms is enough
				delayExecute('msg %s %s' % (word[0], selection), 1)
			elif userdata == 4 and selection != None:
				# xchat.command('say %s' % word[1]) # nope. Hexchat will say this LATER
				delayExecute('say %s' % selection, 1) 
	except Exception:
		# restore status even in case of exception :v
		inProgress = False
		raise

	inProgress = False
	return xchat.EAT_NONE

def selectSub(text):
	import random, os
	text = xchat.strip(text)
	text = text.strip()
	if text.startswith('!select '):
		text = text[(len('!select ')):]
		# if the text contain ',' then consider ',' the separator (unless it's at the end or beginning)
		# None = all white spaces
		if ',' in text.strip(','):
			separator = ','
		else:
			separator = None
		# split and remove empty entries + trim
		selections = []
		for s in text.split(separator):
			s = s.strip()
			if len(s) > 0:
				selections.append(s)
		if len(selections) > 0:
			# get a random number
			random.seed()
			selected = random.randint(0, len(selections)-1)
			return selections[selected]
		else:
			return None

def hookStuff():
	global hookList, eventList
	for event in eventList1:
		hookList.append(xchat.hook_print(event, selectMain, 1))
	for event in eventList2:
		hookList.append(xchat.hook_print(event, selectMain, 2))
	for event in eventList3:
		hookList.append(xchat.hook_print(event, selectMain, 3))
	for event in eventList4:
		hookList.append(xchat.hook_print(event, selectMain, 4))

def unhookStuff():
	global hookList
	for hook in hookList:
		xchat.unhook(hook)
	hookList = []

def controller(word, word_eol, userdata):
	if len(word) > 0:
		if word[1] == 'stop':
			unhookStuff()
		elif word[1] == 'start' or word[1] == 'restart':
			unhookStuff()
			hookStuff()
		elif word[1] == '!select':
			selection = selectSub(word_eol[1])
			if selection != None:
				xchat.command('say %s' % word_eol[1])
				xchat.command('say %s' % selection)
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

def test(word, word_eol, userdata):
	print('Yo')	
	return xchat.EAT_ALL

initStuff()
hookStuff()
# xchat.hook_command("selecttest", test, help="Select test")
xchat.hook_command("select", controller, help="Select controller")
# updateDccListHook = xchat.hook_timer(1000, updateDccList)
# hashFileProcessHook = xchat.hook_timer(1000, hashFileProcess)
xchat.prnt(u'%s v%s plugin loaded' % (__module_name__, __module_version__))