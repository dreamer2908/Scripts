#!/usr/bin/python
# encoding: utf-8

# TODO:
# - Option file

import sys, os, fnmatch, subprocess, time

programName = "MKV Extractor"
version = "0.2"
author = "dreamer2908"

x_video = False
x_audio = False
x_subtitle = True
x_attachment = True
x_chapter = False
x_timecodes = False
x_cuesheet = False
x_tags = False

recursive = False
searchSubFolder = False

mkvtoolnixFolder = r'H:\mkvtoolnix'
mkvmergePath = ''
mkvextractPath = ''
mkvmergePaths = [r'/usr/bin/mkvmerge', r'/usr/sbin/mkvmerge', r'/usr/local/bin/mkvmerge', r'/usr/local/sbin/mkvmerge', r'C:\Program Files (x86)\MKVToolNix\mkvmerge.exe', r'C:\Program Files\MKVToolNix\mkvmerge.exe', r'mkvmerge', r'mkvmerge.exe']
mkvextractPaths = [r'/usr/bin/mkvextract', r'/usr/sbin/mkvextract', r'/usr/local/bin/mkvextract', r'/usr/local/sbin/mkvextract', r'C:\Program Files (x86)\MKVToolNix\mkvextract.exe', r'C:\Program Files\MKVToolNix\mkvextract.exe', r'mkvextract', r'mkvextract.exe']

mkvtoolnixVersion = [ 0, 0, 0 ]

defaultTimer = None
pathList = []
debug = False
fag = []
terminalSupportUnicode = False

# Test if printing unicode characters is possible
def checkUnicodeSupport():
	try:
		text = u'「いなり、こんこん、恋いろは。」番宣ＰＶ'.encode(sys.stdout.encoding)
	except:
		return False
	return True

def removeNonAscii(original):
	result = ''
	for c in original:
		code = ord(c)
		if code < 128:
			result += c
		else:
			result += '?'
	return result

def printReadme():
	print(' ')
	print("%s v%s by %s" % (programName, version, author))
	print(' ')
	print("Syntax: python mkv_extractor.py [options] inputs")
	print(' ')
	print("Input can be individual files, and/or folders.")
	print("  Use Unix shell-style wildcard (*, ?) for the filename pattern.")
	print(' ')
	print("Options:")
	print("  --video                         Extract video tracks")
	print("  --audio                         Extract audio tracks")
	print("  --sub                           Extract subtitle tracks [default: on]")
	print("  --att                           Extract attachments [default: on]")
	print("  --chap                          Extract chapters")
	print("  --timecodes                     Extract timecodes v2")
	print("  --tags                          Extract tags")
	print("  --cuesheet                      Extract cuesheet")
	print("  --no-*                          Do not extract *")
	print("  --mkvtoolnix /path/to/it        Specify mkvtoolnix folder")
	print("  --r                             Also include sub-folder")
	print("  --s                             Also search sub-folder for matching filenames")
	print(' ')
	print('Examples:')
	print('  python mkv_extractor.py \"/home/yumi/Desktop/[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv\"')
	print('  python mkv_extractor.py --audio --chap --r --no-sub ~/Desktop ~/Downloads/*.mkv \"[B63D4DBE].mkv\"')

def parseParams():
	global x_attachment, x_subtitle, x_audio, x_video, x_chapter, x_timecodes, x_tags, x_cuesheet, debug, recursive, mkvtoolnixFolder, pathList
	i = 1
	while i < len(sys.argv):
		arg = sys.argv[i]
		if arg.startswith('-'):
			if arg.startswith('--'):
				arg = arg[2:]
			else:
				arg = arg[1:]
			arg = arg.lower()
			if arg == "sub" or arg == "subtitles":
				x_subtitle = True
			elif arg == "audio":
				x_audio = True
			elif arg == "video":
				x_video = True
			elif arg == "chap":
				x_chapter = True
			elif arg == "att" or arg == "attachments":
				x_attachment = True
			elif arg == "timecodes":
				x_timecodes = True
			elif arg == "tags":
				x_tags = True
			elif arg == "cuesheet":
				x_cuesheet = True
			elif arg == "no-sub" or arg == "no-subtitles":
				x_subtitle = False
			elif arg == "no-audio":
				x_audio = False
			elif arg == "no-video":
				x_video = False
			elif arg == "no-chap":
				x_chapter = False
			elif arg == "no-att" or arg == "no-attachments":
				x_attachment = False
			elif arg == "no-timecodes":
				x_timecodes = False
			elif arg == "no-tags":
				x_tags = False
			elif arg == "no-cuesheet":
				x_cuesheet = False
			elif arg == "mkvtoolnix" and i < len(sys.argv) - 1:
				mkvtoolnixFolder = sys.argv[i+1]
				i += 1
			elif arg == "r":
				recursive = True
			elif arg == "s":
				searchSubFolder = True
			elif arg == "d" or arg == "debug":
				debug = True
		else:
			pathList.append(arg)
		i += 1

# detect mkvmerge/extract path and some miscs
def detectPaths():
	global mkvmergePath, mkvextractPath, mkvtoolnixFolder, mkvextractPaths, mkvmergePaths

	mkvmergePath = ''
	mkvextractPath = ''

	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	if sys.platform == 'win32':
		merge = 'mkvmerge.exe'
		extract = 'mkvextract.exe'
	else:
		merge = 'mkvmerge'
		extract = 'mkvextract'

	# Check if mkvtoolnixFolder works
	if is_exe(os.path.join(mkvtoolnixFolder, merge)) and is_exe(os.path.join(mkvtoolnixFolder, extract)):
		mkvmergePath = os.path.join(mkvtoolnixFolder, merge)
		mkvextractPath = os.path.join(mkvtoolnixFolder, extract)
		return

	# Check if they're in paths
	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		mergeP = os.path.join(path, merge)
		extractP = os.path.join(path, extract)
		if is_exe(mergeP) and is_exe(extractP):
			mkvmergePath = mergeP
			mkvextractPath = extractP
			return

	# Check if those common paths work
	for p in mkvmergePaths:
		if (os.path.isfile(p)):
			mkvmergePath = p
			break
	for p in mkvextractPaths:
		if (os.path.isfile(p)):
			mkvextractPath = p
			break

def getMkvToolnixVersion():
	global mkvtoolnixVersion, mkvmergePath

	params = [mkvmergePath, '--version']

	if debug:
		print('getMkvToolnixVersion: params')
		print(params)

	rawInfo = ''
	try:
		rawInfo = subprocess.check_output(params)
	except subprocess.CalledProcessError as e:
		print(e.cmd)
		rawInfo = e.output
	if sys.stdout.encoding != None:
		rawInfo = rawInfo.decode(sys.stdout.encoding)

	if debug:
		print('getMkvToolnixVersion: rawInfo')
		print(rawInfo)

	elements = rawInfo.split()
	versionString = elements[1][1:]
	v1 = 0
	v2 = 0
	v3 = 0
	pos = 0
	for i in range(len(versionString) - 1):
		if versionString[i] == '.':
			if pos < i:
				if v1 == 0:
					v1 = int(versionString[pos:i])
				elif v2 == 0:
					v2 = int(versionString[pos:i])
				else:
					v3 = int(versionString[pos:i])
			pos = i + 1

	mkvtoolnixVersion = [ v1, v2, v3 ]
	if debug:
		print(mkvtoolnixVersion)

def checkSanity():
	global terminalSupportUnicode, mkvmergePath, mkvextractPath, debug, pathList

	if debug:
		print('terminalSupportUnicode = %s' % terminalSupportUnicode)

	if len(pathList) < 1: # no imput
		printReadme()
		if (mkvmergePath == '' or mkvextractPath == ''):
			print('\nmkvtoolnix not found!')
		sys.exit()

def revertEscapeSeq(text):
	escaped = ['\\s', '\\2', '\\c', '\\h', '\\\\']
	org = [' ', '"', ':', '#', '\\']
	result = text
	for i in range(len(escaped)):
		result = result.replace(escaped[i], org[i])
	return result

def getExt(codec_id):
	# Better performance, I guess
	if codec_id.startswith('V_'):
		if codec_id == 'V_MPEG4/ISO/AVC':
			return 'h264'
		elif codec_id == 'V_MS/VFW/FOURCC':
			return 'avi'
		elif codec_id.startswith('V_REAL/'):
			return 'rm'
		elif codec_id == 'V_THEORA':
			return 'ogg'
		elif codec_id == 'V_VP8' or codec_id == 'V_VP9':
			return 'ivf'
	elif codec_id.startswith('A_'):
		if codec_id == 'A_MPEG/L2':
			return 'mp2'
		elif codec_id == 'A_MPEG/L3':
			return 'mp3'
		elif codec_id == 'A_AC3':
			return 'ac3'
		elif codec_id == 'A_PCM/INT/LIT':
			return 'wav'
		elif codec_id.startswith('A_AAC'):
			return 'aac'
		elif codec_id == 'A_VORBIS':
			return 'ogg'
		elif codec_id.startswith('A_REAL/'):
			return 'rm'
		elif codec_id == 'A_TTA1':
			return 'tta'
		elif codec_id == 'A_ALAC':
			return 'alac'
		elif codec_id == 'A_FLAC':
			return 'flac'
		elif codec_id == 'A_WAVPACK4':
			return 'wv'
		elif codec_id == 'A_OPUS':
			return 'opus'
	elif codec_id.startswith('S_'):
		if codec_id == 'S_TEXT/UTF8':
			return 'srt'
		elif codec_id == 'S_TEXT/SSA':
			return 'ssa'
		elif codec_id == 'S_TEXT/ASS':
			return 'ass'
		elif codec_id == 'S_KATE':
			return 'ogg'
		elif codec_id == 'S_VOBSUB':
			return 'sub'
		elif codec_id == 'S_TEXT/USF':
			return 'usf'
		elif codec_id == 'S_HDMV/PGS':
			return 'sub'
	else:
		return 'unknown'

def getFileInfo(fileName):
	global mkvmergePath, debug

	rawInfo = ''
	try:
		rawInfo = subprocess.check_output([mkvmergePath, '-I', fileName])
	except subprocess.CalledProcessError as e:
		rawInfo = e.output

	if sys.stdout.encoding != None:
		rawInfo = rawInfo.decode(sys.stdout.encoding)

	# Tested on Windows 7 x64 + mkvToolnix 6.6, and LinuxMint 15 x64 + mkvToolnix 6.3
	# mkvmerge seems to use EOL \r\r\n on win32 and \n on linux. Dunno others
	if '\r\r\n' in rawInfo: # and sys.platform == 'win32'
		rawInfo = rawInfo.split('\r\r\n')
	else:
		rawInfo = rawInfo.split('\n')

	format = ''
	tracks = []
	tracks_v = []
	tracks_a = []
	tracks_s = []
	attachments = []
	chapters = 0

	for i in range(len(rawInfo)):
		line = rawInfo[i]

		if line.startswith('File'):
			elements = line.split()
			for i in range(len(elements)):
				if elements[i] == 'container:':
					format = elements[i + 1]
					break

		elif line.startswith('Attachment ID'):
			elements = line.split()
			ID = int(elements[2][:-1])
			mimeType = 'application/x-truetype-font'
			size = 0
			storedFname = ''

			elements = line.split("'")
			storedFname = revertEscapeSeq(elements[len(elements) - 2])

			attachment = (ID, mimeType, size, storedFname)
			attachments.append(attachment)

		elif line.startswith('Track ID'):
			elements = line.split()

			ID = int(elements[2][:-1])
			trackType = elements[3]
			codec_id = ''
			track_name = ''
			language = ''

			for e in elements:
				if e.startswith('codec_id:'):
					codec_id = e[9:]
				elif e.startswith('track_name:'):
					track_name = revertEscapeSeq(e[11:])
				elif e.startswith('language:'):
					language = e[9:]

			if debug:
				print('ID: %d: Track type: %s, codec ID: "%s", track name: "%s", language: "%s"' % (ID, trackType, codec_id, track_name, language))

			track = (ID, trackType, codec_id, track_name, language)
			tracks.append(track)

			# There are only these types for tracks atm. Don't use else for the last 'cause mkvtoolnix's development is not predictable
			if trackType == 'video':
				tracks_v.append(track)
			elif trackType == 'audio':
				tracks_a.append(track)
			elif trackType == 'subtitles':
				tracks_s.append(track)

		elif line.startswith('Chapters'):
			elements = line.split()
			chapters = int(elements[1])

	if debug:
		print('getFileInfo: rawInfo')
		print(rawInfo)
		print(' ')
		print('getFileInfo: output')
		print(format, tracks, tracks_v, tracks_a, tracks_s, attachments, chapters)

	fileInfo = fileName, format, tracks, tracks_v, tracks_a, tracks_s, attachments, chapters
	return fileInfo

def extractIt(fileInfo):
	global x_attachment, x_subtitle, x_audio, x_video, x_chapter, x_timecodes, x_cuesheet, x_tags, mkvextractPath, debug
	(fileName, format, tracks, tracks_v, tracks_a, tracks_s, attachments, chapters) = fileInfo

	# reject invalid inputs
	if not format == 'Matroska':
		print('"%s" is not a Matroska file!' % fileName)
		return

	namae, ext = os.path.splitext(fileName)

	if debug:
		print('x_audio = %s' % x_audio)
		print('x_video = %s' % x_video)
		print('x_subtitle = %s' % x_subtitle)
		print('x_attachment = %s' % x_attachment)

	if x_subtitle or x_audio or x_video:
		params = [mkvextractPath, 'tracks', fileName]
		if x_video:
			for track in tracks_v:
				(ID, trackType, codec_id, track_name, language) = track
				params.append('%d:%s_Track%02d.%s' % (ID, namae, ID, getExt(codec_id)))
		if x_audio:
			for track in tracks_a:
				(ID, trackType, codec_id, track_name, language) = track
				params.append('%d:%s_Track%02d.%s' % (ID, namae, ID, getExt(codec_id)))
		if x_subtitle:
			for track in tracks_s:
				(ID, trackType, codec_id, track_name, language) = track
				params.append('%d:%s_Track%02d_%s.%s' % (ID, namae, ID, language, getExt(codec_id)))

		if debug:
			print('extractIt: tracks: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: tracks: rawInfo')
			print(rawInfo)

	if x_attachment:
		params = [mkvextractPath, 'attachments', fileName]
		for attachment in attachments:
			(ID, mimeType, size, storedFname) = attachment
			params.append('%d:%s' % (ID, os.path.join(namae + '_Attachments', storedFname)))

		if debug:
			print('extractIt: attachments: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: attachments: rawInfo')
			print(rawInfo)

	if x_chapter and chapters > 0:
		params = [mkvextractPath, 'chapters', fileName]
		params.append('--redirect-output')
		params.append(namae + '_Chapters.xml')

		if debug:
			print('extractIt: x_chapter: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: x_chapter: rawInfo')
			print(rawInfo)

	if x_timecodes:
		params = [mkvextractPath, 'timecodes_v2', fileName]
		for track in tracks:
			(ID, trackType, codec_id, track_name, language) = track
			params.append('%d:%s_Track%02d.timecodes.txt' % (ID, namae, ID))

		if debug:
			print('extractIt: x_timecodes: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: x_timecodes: rawInfo')
			print(rawInfo)

	if x_tags:
		params = [mkvextractPath, 'tags', fileName]
		params.append('--redirect-output')
		params.append(namae + '_Tags.xml')

		if debug:
			print('extractIt: x_tags: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: x_tags: rawInfo')
			print(rawInfo)

	if x_cuesheet:
		params = [mkvextractPath, 'cuesheet', fileName]
		params.append('--redirect-output')
		params.append(namae + '_Cuesheet.cue')

		if debug:
			print('extractIt: x_cuesheet: params')
			print(params)

		rawInfo = ''
		try:
			rawInfo = subprocess.check_output(params)
		except subprocess.CalledProcessError as e:
			# print(e.cmd)
			rawInfo = e.output
		if sys.stdout.encoding != None:
			rawInfo = rawInfo.decode(sys.stdout.encoding)

		if debug:
			print('extractIt: x_cuesheet: rawInfo')
			print(rawInfo)

def processFile(fileName):
	global terminalSupportUnicode, fag

	# Not gonna trust the caller completely
	if not os.path.isfile(fileName):
		fag.append(fileName)
		return

	# In Python 2, decode the path to unicode string
	# In python 3, it's already unicode, so don't
	if sys.version_info[0] < 3 and hasattr(fileName, 'decode'):
		fileName = fileName.decode(sys.getfilesystemencoding())

	# deal with terminal encoding mess
	if not terminalSupportUnicode:
		fileName = removeNonAscii(fileName)

	fileInfo = getFileInfo(fileName)
	extractIt(fileInfo)
	#print('%s... Done!' % (fileName))

def processFolderv2(path):
	global recursive, searchSubFolder

	pattern = '*'
	usePattern = False

	# Check if the input is an existing folder.
	# If not, split the path and check if "folder" exists
	if not os.path.isdir(path):
		folder, pattern = os.path.split(path)
		if os.path.isdir(folder):
			path = folder
			usePattern = True
		elif folder == '':
			path = os.getcwd()
			usePattern = True
		else:
			return

	for (dirpath, dirnames, filenames) in os.walk(path):
		if usePattern:
			filenames = patternMatching(filenames, pattern)
		for fname in filenames:
			processFile(os.path.join(dirpath, fname))
		if (not usePattern and not recursive) or (usePattern and not searchSubFolder):
			break

def patternMatching(filenames, pattern):
	import re

	#pattern = 'C?*apter?.txt'
	matchingFname = []

	if not ('*' in pattern or  '?' in pattern):
		return []

	def convertPatternToRegex(pattern):
		specialChars = '.^$*+?{}, \\[]|():=#!<'
		regex = ''

		# convert to unicode string first
		# just assume all utf-8 -- this file is in this encoding anyway
		if hasattr(pattern, 'decode'):
			pattern = pattern.decode('utf-8')

		# parse pattern
		for i in range(len(pattern)):
			char = pattern[i]
			if char == '*' or char == '?':
				if char == '?':
					regex += '.'
				elif char == '*':
					regex += '(.*)'
			else:
				# escape stuff
				if char in specialChars:
					regex += '\\'
				regex += char
				if i == len(pattern) - 1: # end of pattern. Fixed a bug that made pattern blablah*.mkv match blablah.mkv.pass
					regex += '$'

		return regex

	regPattern = convertPatternToRegex(pattern)
	if debug:
		print(regPattern)
	regObject = re.compile(regPattern)

	for fname in filenames:
		match = regObject.match(fname)
		if match:
			matchingFname.append(fname)

	if debug:
		print(matchingFname)

	return matchingFname

# Process files and folders
def doStuff():
	global debug, pathList

	print('Processing %d input(s)...\n' % len(pathList))
	if debug:
		print(pathList)

	for path in pathList:
		if os.path.isfile(path):
			processFile(path) # processFolderv2 also works with file, but this saves some cpu circles
		elif (path.endswith(os.sep) or path.endswith("'") or path.endswith('"')) and os.path.isdir(path[:-1]):
			processFolderv2(path[:-1])
		else:
			processFolderv2(path)
		print('"%s" Done!' % path)

	print('\nAll done.')

def initStuff():
	global defaultTimer, terminalSupportUnicode

	terminalSupportUnicode = checkUnicodeSupport()
	
	# Stats setup
	if sys.platform == 'win32':
	    # On Windows, the best timer is time.clock
	    defaultTimer = time.clock
	else:
	    # On most other platforms the best timer is time.time
	    defaultTimer = time.time

	detectPaths()
	getMkvToolnixVersion()

parseParams()
initStuff()
checkSanity()
doStuff()