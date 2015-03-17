#!/usr/bin/python
# encoding: utf-8

__module_name__ = "Hexchat Flip Plugin"
__module_version__ = "0.1.2"
__module_description__ = "Flip command"
__author__ = "dreamer2908"

import sys
import xchat as XC # works with both xchat and hexchat
# import hexchat # this works only in hexchat

def flipChar(c):
	if c == u'a':
		return u'ɐ'
	elif c == u'b':
		return u'q'
	elif c == u'c':
		return u'ɔ'
	elif c == u'd':
		return u'p'
	elif c == u'e':
		return u'ǝ'
	elif c == u'f':
		return u'ɟ' 
	elif c == u'g':
		return u'ƃ' # u'b'
	elif c == u'h':
		return u'ɥ'
	elif c == u'i':
		return u'ı' #'\u0131\u0323' 
	elif c == u'j':
		return u'ɾ' #u'ظ'
	elif c == u'k':
		return u'ʞ'
	elif c == u'l':
		return u'ן'
	elif c == u'm':
		return u'ɯ'
	elif c == u'n':
		return u'u'
	elif c == u'o':
		return u'o'
	elif c == u'p':
		return u'd'
	elif c == u'q':
		return u'b'
	elif c == u'r':
		return u'ɹ'
	elif c == u's':
		return u's'
	elif c == u't':
		return u'ʇ'
	elif c == u'u':
		return u'n'
	elif c == u'v':
		return u'ʌ'
	elif c == u'w':
		return u'ʍ'
	elif c == u'x':
		return u'x'
	elif c == u'y':
		return u'ʎ'
	elif c == u'z':
		return u'z'
	elif c == u'[':
		return u']'
	elif c == u']':
		return u'['
	elif c == u'(':
		return u')'
	elif c == u')':
		return u'('
	elif c == u'{':
		return u'}'
	elif c == u'}':
		return u'{'
	elif c == u'?':
		return u'¿'
	elif c == u'¿':
		return u'?'
	elif c == u'!':
		return u'¡'
	elif c == u"\'":
		return u','
	elif c == u',':
		return "\'"
	elif c == u'.':
		return u'˙'
	elif c == u'_':
		return u'‾'
	elif c == u';':
		return u'؛'
	elif c == u'9':
		return u'6'
	elif c == u'6':
		return u'9'
	else: 
		if sys.version_info[0] < 3:
			return unicode(c)
		else:
			return str(c)

def flipString(text):
	result = u''
	length = len(text)
	text = text.lower()
	for i in range(length):
		result += flipChar(text[length - i - 1])
	return result

def flips(word, word_eol, userdata):
	try:
		if len(word) > 1:
			text = u' '.join(word[1:])
			XC.command(u'me ' + u'flips ' + flipString(text))
		else:
			XC.prnt('Pls use "/flip whatever text"')
	except Exception as e:
		if sys.version_info[0] < 3:
			error = unicode(e)
		else:
			error = str(e)
		print('Error: %s' % error)
	return XC.EAT_ALL

def flipRus(word, word_eol, userdata):
	XC.command('say In Soviet Russia, the Table flips you ノ┬─┬ノ ︵ ( \o°o)\ ')
	return XC.EAT_ALL

def printTest():
	import time
	time.sleep(0.5)
	try:
		XC.prnt(flipString(u'the quick brown fox jumps over the lazy dog'))
	except Exception as e:
		XC.prnt(u"Couldn't print the test line: %s" % e)

XC.hook_command("flip", flips, help='FLIP IT!')
XC.hook_command("fliprus", flipRus, help='In Soviet Russia, the Table flips you')
XC.prnt(__module_name__ + ' version ' + __module_version__ + ' loaded.')
printTest()

# In Soviet Russia, the Table flips you ノ┬─┬ノ ︵ ( \o°o)\