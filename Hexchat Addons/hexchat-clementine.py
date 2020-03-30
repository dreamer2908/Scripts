#!/usr/bin/python
# encoding: utf-8

__module_name__ = "(He)xchat Clementine Now Playing"
__module_version__ = "1.1"
__module_description__ = "Get NP information from Clementine"

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

def getClemIFace():
	from dbus import Bus, DBusException
	bus = Bus(Bus.TYPE_SESSION)
	try:
		return bus.get_object('org.mpris.clementine', '/Player')
	except: # DBusException: # catch all exeptions
		xchat.prnt("Either Clementine is not running or you have something wrong with your D-Bus setup.")
		return None

def getValue(clemMData, key, keyFB, default):
	try:
		return clemMData[key]
	except KeyError:
		try:
			return clemMData[keyFB]
		except:
			return default
	except:
		return default

def toUtf8(text):
	return unicode(text).encode('utf-8')

def getNpInfo():
	global position, artist, album, tracknumber, title, bitrate, samplerate, length, fmt

	clemIFace = getClemIFace()

	if clemIFace != None:
		clemMData = clemIFace.GetMetadata()
		try:
			position = clemIFace.PositionGet() / 1000 
		except:
			position = 0
		artist = getValue(clemMData, 'artist', '', None)
		album = getValue(clemMData, 'album', '', None)
		tracknumber = getValue(clemMData, 'tracknumber', '', -1)
		title = getValue(clemMData, 'title', '', '')
		bitrate = '%d kbps' % getValue(clemMData, 'bitrate', 'audio-bitrate', 0)
		samplerate = '%d Hz' % getValue(clemMData, 'audio-samplerate', '', 0)
		length = getValue(clemMData, 'time', '', 0)

		# get format from file extention
		location = getValue(clemMData, 'location', '', '')
		namae, ext = os.path.splitext(location)
		if len(ext) > 0:
			fmt = ext.upper().strip('.')
		else:
			fmt = 'Unknown'

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
			text = "me is playing nothing on Clementine"
		else:
			text = "me is playing on Clementine: "
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
			text = "me is playing nothing on Clementine"
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
 
xchat.hook_command("NP", nowPlaying, help="Displays current playing song (long).")
xchat.hook_command("NP2", nowPlaying2, help="Displays current playing song (short).")
xchat.prnt(u'%s v%s plugin loaded' % (__module_name__, __module_version__))