#!/usr/bin/python
# encoding: utf-8

__module_name__ = "(He)xchat Audacious Now Playing"
__module_author__ = "dreamer2908"
__module_version__ = "1.0"
__module_description__ = "Get NP information from Audacious"

import xchat, sys, os, math

position = 0
length = 0
artist = u''
album = u''
tracknumber = 0
title = u''
bitrate = 0
samplerate = 0
fmt = u''
quality = u''

def getAuIFace():
	from dbus import Bus, DBusException
	bus = Bus(Bus.TYPE_SESSION)
	try:
		return bus.get_object('org.mpris.audacious', '/Player')
	except: # DBusException: # catch all exceptions
		xchat.prnt("Either Audacious is not running or you have something wrong with your D-Bus setup.")
		return None

def getValue(auData, key, keyFB, default):
	try:
		return auData[key]
	except KeyError:
		try:
			return auData[keyFB]
		except:
			return default
	except:
		return default

def toUtf8(text):
	return unicode(text).encode('utf-8')

def getNpInfo():
	import urllib
	global position, artist, album, tracknumber, title, bitrate, samplerate, length, fmt, quality

	auIFace = getAuIFace()

	if auIFace != None:
		auData = auIFace.GetMetadata()
		try:
			position = auIFace.PositionGet() / 1000 
		except:
			position = 0
		artist = getValue(auData, 'artist', '', None)
		album = getValue(auData, 'album', '', None)
		tracknumber = getValue(auData, 'tracknumber', '', -1)
		title = getValue(auData, 'title', '', '')
		bitrate = '%d kbps' % getValue(auData, 'bitrate', 'audio-bitrate', 0)

		# dbus.String(u'quality'): dbus.String(u'Stereo, 44100 Hz', variant_level=1),
		quality = getValue(auData, 'quality', '', "Stereo, 0 Hz")
		tmp = quality.split(', ')
		samplerate = tmp[len(tmp) - 1]
		length = getValue(auData, 'mtime', '', 0) / 1000

		# get format from file extention
		# or dbus.String(u'codec'): dbus.String(u'MPEG-1 layer 3', variant_level=1),
		location = urllib.unquote(getValue(auData, 'location', '', ''))
		namae, ext = os.path.splitext(location)
		if len(ext) > 0:
			fmt = ext.upper().strip('.')
		else:
			fmt = 'Unknown'
		
		if len(title) < 1:
			dirName, fileName = os.path.split(location)
			title = fileName

		return True 
	return False

def formatTime(time):
	if time >= 3600:
		result = '%d:' % math.floor(time / 3600)
	else:
		result = ''
	time = time % 3600
	result += '%02d' % math.floor(time / 60)
	time = time % 60
	result += ':%02d' % math.floor(time)
	return result

def nowPlaying(word, word_eol, userdata):
	if getNpInfo():	 
		if len(title) < 1:
			text = "me is playing nothing on Audacious"
		else:
			text = "me is playing on Audacious: "
			text += '[ %s / %s ] ' % (formatTime(position), formatTime(length))

			text += '\"' + title + '\" '
			if artist != None:
				text += 'by "%s" ' % artist
			elif album != None:
				text += 'by "Unknown artist" '

			if album != None:
				if tracknumber > 0:
					text += '(track #%d' % tracknumber + ' of album \"' + album + '\") '
				else:
					text += '(album \"' +  album + '\") '

			text += '| ' + fmt + ' | ' + samplerate + ' | ' + bitrate

		xchat.command(text)

	return xchat.EAT_ALL


def nowPlaying2(word, word_eol, userdata):
	if getNpInfo():	 
		if len(title) < 1:
			text = "me is playing nothing on Audacious"
		else:
			text = "me > "

			if artist != None:
				text += '%s - ' % artist
			elif album != None:
				text += 'Unknown artist - '

			text += '%s ' % title

			if album != None:
				if tracknumber > 0:
					text += ' - [ %s #%d ] ' % (album, tracknumber)
				else:
					text += ' - [ %s ] ' % (album)

			text += '- [ %s / %s ] ' % (formatTime(position), formatTime(length))

		xchat.command(text)

	return xchat.EAT_ALL

def test(word, word_eol, userdata):
	auIFace = getAuIFace()
	auData = auIFace.GetMetadata()
	print(auData)
	print(auIFace.PositionGet())
	
	return xchat.EAT_ALL
 
xchat.hook_command("aud", nowPlaying, help="Displays current playing song in Audacious (long).")
xchat.hook_command("aud2", nowPlaying2, help="Displays current playing song in Audacious (short).")
xchat.hook_command("audt", test, help="Test Audacious")
xchat.prnt(u'%s v%s plugin loaded' % (__module_name__, __module_version__))