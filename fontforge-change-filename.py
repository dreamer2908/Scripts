#!/usr/bin/python
# encoding: utf-8

import fontforge, os, sys

programName = "Font filename changer"
version = "0.1"
author = "dreamer2908"

defaultTimer = None
terminalSupportUnicode = False
python2 = False
win32 = False
debug = False

inputList = []
outputDir = ''
outputFmt = []
autoDetectAll = False
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

def printInfo(font):
	print('font.familyname: ' + font.familyname)
	#print('font.fondname: ' + font.fondname)
	print('font.fontname: ' + font.fontname)
	print('font.fullname: ' + font.fullname)
	sfnt_names = list(font.sfnt_names)
	for i in range(len(sfnt_names)):
		print(sfnt_names[i])

def parseParams():
	global inputList, outputDir, outputFmt, autoDetectAll

	fileBaseName = ''
	familyName = ''	

	i = 1
	argsCount = len(sys.argv)
	allInputs = False
	while i < argsCount:
		arg = sys.argv[i]
		if arg.startswith('-') and not allInputs:
			if arg.startswith('--'):
				arg = arg[2:]
			else:
				arg = arg[1:]
			arg = arg.lower()
			
			if arg == "f" and i < argsCount - 1:
				familyName = sys.argv[i+1]
				i += 1
			elif arg == "b" and i < argsCount - 1:
				fileBaseName = sys.argv[i+1]
				i += 1
			elif arg == "o" and i < argsCount - 1:
				outputDir = sys.argv[i+1]
				i += 1
			elif arg == "fmt" and i < argsCount - 1:
				fmts = sys.argv[i+1].split(',')
				for fmt in fmts:
					outputFmt.append(fmt)
				i += 1
			elif arg == "d":
				familyName = ''
				fileBaseName = ''
			elif arg == "i":
				allInputs = True
			elif arg == 'da':
				autoDetectAll = True
		else:
			tmp = (arg, fileBaseName, familyName)
			inputList.append(tmp)
		i += 1

def checkSanity():
	import sys
	global outputFmt, outputDir, inputList

	if not os.path.isdir(outputDir):
		try:
			os.makedirs(outputDir)
		except:
			pass

	sane = len(inputList) > 0
	if not sane:
		printReadMe()
		sys.exit()

def printReadMe():
	print(' ')
	print("%s v%s by %s" % (programName, version, author))
	print(' ')
	print("Syntax: fontforge -script fontforge-naming-fix.py [options] inputs [[optioms] [inputs]]")
	print(' ')
	print("Options:")
	print('    -f "font family name"            Set font family name')
	print('    -b "family part of filename"     Set base filename')
	print('    -o "output directory"            Set where to save outputs')
	print('    -fmt "otf,ttf,sfd"               Set output formats via file extension')
	print("    -d                               Auto-detect family name and base filename")
	print("    -da                              Ignore all specified family names and base names and try to auto-detect them")
	print("    -i                               All following paramemters are inputs")
	print(' ')
	print('Note:')
	print('    Options (except for da) take effect on inputs following them.')
	print('    Option d sets f and b to blank. Auto-detecting works only when the filename is FamilyName-StyleName.ext.')
	print('    Ignoring all specified family names and base names and auto-detecting everything *might* work ')
	print('        if and only if all inputs come from the same family and are named in the same way.')
	print('        The longest common string will be chosen as family name and base filename.')
	print('        For example, with Erato Light Italic.woff, Erato Light.woff, Erato Regular.woff; we get "Erato"')
	print('    Output directory is <current working directory> by default.')
	print('    If not specified, output format is the same as input if it\' either otf, ttf, or sfd; otf otherwise.')
	print(' ')
	print("Examples:")
	print('    fontforge -script fontforge-naming-fix.py -fmt "otf,ttf" -f "Erato" -d "Erato" "Erato Light Italic.woff" -d "TitilliumWeb-SemiBoldItalic.ttf"')

def doStuff2():
	global inputList, outputFmt, outputDir, autoDetectAll

	print(' ')
	print("%s v%s by %s" % (programName, version, author))

	for item in inputList:
		fileName = item[0]
		fileBaseName = item[1]
		familyName = item[2]

		print('\nProcessing file: %s' % fileName)
		if not os.path.isfile(fileName):
			print('Couldn\'t find the file %s' % fileName)
			continue

		folder, fname = os.path.split(fileName)
		ext = os.path.splitext(fname)[1]

		# for pirate stuff
		if not ext:
			ext = '.woff'
		elif len(ext) < 3:
			try:
				dump = int(ext)
				ext = '.woff'
			except:
				pass

		font = fontforge.open(fileName)
		font_fullname = font.fullname
		font_psname = font.fontname
		font_familyname = font.familyname
		font.close()

		os.rename(fileName, os.path.join(folder, font_psname) + ext)

	print('\nAll done.')

initStuff()
parseParams()
checkSanity()
doStuff2()