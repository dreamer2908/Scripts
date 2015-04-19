#!/usr/bin/python
# encoding: utf-8

# TODO: 
# - figure out how to change Embeddable, Italic, Bold
# - make fixFontName() smarter. Current (not good): StuartPro-TitlingBoldItalic -> family "Stuart Pro Titling Bold", style "Italic"
# - support "super" family name. Ex: "Stuart Pro" for "Stuart Pro Titling", "Stuart Pro Text", "Stuart Pro Caption"
# 
# Note:
# - Found the issue with Bold & Italic: the March 2015 release of FontForge is buggy. February 2015 one works just fine.

import fontforge, os, sys

programName = "Font naming fixer"
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

# exceptions
do_not_change_book_to_regular = True

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

def renameFont(font, s1, s2):
	if font.familyname:
		font.familyname = font.familyname.replace(s1, s2)
	if font.fondname:
		font.fondname = font.fondname.replace(s1, s2)
	if font.fontname:
		font.fontname = font.fontname.replace(s1, s2)
	if font.fullname:
		font.fullname = font.fullname.replace(s1, s2)

	sfnt_names = list(font.sfnt_names)
	for i in range(len(sfnt_names)):
		if not s2 in sfnt_names[i][2]:
			sfnt_names[i] = list(sfnt_names[i]) # huehuehue
			sfnt_names[i][2] = sfnt_names[i][2].replace(s1, s2)
			sfnt_names[i] = tuple(sfnt_names[i])

	font.sfnt_names = tuple(sfnt_names)

def fixFontName(font, familyName, styleName):
	# needs to change some params
	if True:
		if (styleName == 'Regular Italic'):
			styleName = 'Italic'
		elif styleName == 'Book Italic' and not do_not_change_book_to_regular:
			styleName = 'Italic'
		elif (styleName == 'Normal Italic'):
			styleName = 'Italic'

	font.familyname = familyName
	font.fontname = (familyName + '-' + styleName).replace(' ', '')
	font.fullname = familyName + ' ' + styleName
	font.fondname = font.fullname.replace('-', ' ')

	### Old code, before I notice font.appendSFNTName. Might be useful for something else ###
	### Back to old code because of the protential issue ###

	sfnt_names = []
	for tmp in font.sfnt_names: # remove all name-related records
		if tmp[1] != 'Family' and tmp[1] != 'SubFamily' and tmp[1] != 'Fullname' and tmp[1] != 'PostScriptName' and tmp[1] != 'Preferred Family' and tmp[1] != 'Preferred Styles' and tmp[1] != 'Compatible Full':
			sfnt_names.append(tmp)
	
	# put style link group here
	Family = familyName
	if not (styleName == 'Italic' or styleName == 'Bold' or styleName == 'Bold Italic' or 'Regular' == styleName or ('Book' == styleName and not do_not_change_book_to_regular) or 'Normal' == styleName or 'Roman' == styleName):
		Family = familyName + ' ' + styleName.replace('Italic', '').replace('Regular', '')
		if not do_not_change_book_to_regular:
			Family = Family.replace('Book', '')
		Family = Family.replace('Normal', '').replace('Roman', '')
		Family = Family.replace('  ', ' ').strip()
	ttf_Family = ('English (US)', 'Family', Family)
	# The 'Style Name' field must have one of the four values: 'Regular', 'Italic', 'Bold', 'Bold Italic'. No other values are acceptable. 
	SubFamily = 'Regular'
	if styleName == 'Bold Italic' or styleName == 'Bold' or styleName == 'Italic' or styleName == 'Regular':
		SubFamily = styleName
	elif 'Italic' in styleName:
		SubFamily = 'Italic'
	ttf_SubFamily = ('English (US)', 'SubFamily', SubFamily)
	ttf_Fullname = ('English (US)', 'Fullname', font.fullname)
	ttf_PostScriptName = ('English (US)', 'PostScriptName', font.fontname)
	ttf_PreferredFamily = ('English (US)', 'Preferred Family', familyName)
	ttf_PreferredStyles = ('English (US)', 'Preferred Styles', styleName)
	ttf_CompatibleFull = ('English (US)', 'Compatible Full', font.fullname)

	sfnt_names.append(ttf_Family)
	sfnt_names.append(ttf_SubFamily)
	sfnt_names.append(ttf_Fullname)
	sfnt_names.append(ttf_PostScriptName)
	sfnt_names.append(ttf_PreferredFamily)
	sfnt_names.append(ttf_PreferredStyles)
	sfnt_names.append(ttf_CompatibleFull)

	font.sfnt_names = tuple(sfnt_names)

	# ### New code, use font.appendSFNTName instead of font.sfnt_names ###
	# ### Might have problems if it has something else rather than English (US) like Japanese fonts ##

	# # put style link group here
	# Family = familyName
	# if not ((styleName == 'Italic') or (styleName == 'Bold') or (styleName == 'Bold Italic') or ('Regular' in styleName) or ('Book' in styleName) or ('Normal' in styleName) or ('Roman' in styleName)):
	# 	Family = familyName + ' ' + styleName.replace('Italic', '').strip()
	# font.appendSFNTName('English (US)', 'Family', Family)

	# # The 'Style Name' field must have one of the four values: 'Regular', 'Italic', 'Bold', 'Bold Italic'. No other values are acceptable. 
	# SubFamily = 'Regular'
	# if ((styleName == 'Bold Italic') or (styleName == 'Bold') or (styleName == 'Italic') or (styleName == 'Regular')):
	# 	SubFamily = styleName
	# elif ('Italic' in styleName):
	# 	SubFamily = 'Italic'

	# font.appendSFNTName('English (US)', 'SubFamily', SubFamily)
	# font.appendSFNTName('English (US)', 'Fullname', font.fullname)
	# font.appendSFNTName('English (US)', 'PostScriptName', font.fontname)
	# font.appendSFNTName('English (US)', 'Preferred Family', familyName)
	# font.appendSFNTName('English (US)', 'Preferred Styles', styleName)
	# font.appendSFNTName('English (US)', 'Compatible Full', font.fullname)

def fixFontWeight(font, styleName):
	styleName = styleName.replace('Italic', '').strip()

	lookupStr = ('None', 'Hair', 'Hairline', 'Thin', 'UltraLight', 'Ultra Light', 'ExtraLight',  'Extra Light', 'Light', 'Lt', 'Regular', 'Book', 'Normal', 'Medium', 'SemiBold', 'Semi Bold', 'DemiBold', 'SmB', 'SemiB', 'ExtraBold', 'Extra Bold', 'XB', 'XtraB', 'Bold', 'Heavy', 'Black', 'Ultra')
	lookupNum = (   400,    100,        100,    100,          200,           200,          200,            200,     300,  300,       400,    400,      400,      500,        600,         600,        600,   600,     600,         800,          800,  800,     800,    700,     800,     900,    900)

	sWeight = 'Regular'
	nWeight = 400
	matched = False
	for i in range(len(lookupStr)): # safe first
		# print('lookupStr[i] = "%s". styleName = "%s"' % (lookupStr[i], styleName))
		if (lookupStr[i] == styleName):
			sWeight = lookupStr[i]
			nWeight = lookupNum[i]
			matched = True
			break
	if not matched:
		for i in range(len(lookupStr)):
			if (lookupStr[i].lower() in styleName.lower()):
				sWeight = lookupStr[i]
				nWeight = lookupNum[i]
				break

	font.os2_weight = nWeight
	font.weight = sWeight

	# print('sWeight = "%s"' % sWeight)
	# print('nWeight = %d' % nWeight)

def fixFontMisc(font, styleName):
	os2_version = font.os2_version
	if os2_version < 2: # windows will reject otf cff font with os2 version 1
		font.os2_version = 3

	# macstyle is not documented at all. After a few tests, these work. 
	# I have no idea about other things in macstyle, but atm, I only need to set Bold and Italic.
	# OK, apparently it's not enough. It works in FontForge project but not when it generates fonts.
	# Now I have even less idea about this than previously
	if styleName == 'Bold Italic':
		font.macstyle = 3
	elif styleName == 'Bold':
		font.macstyle = 1
	elif 'Italic' in styleName:
		font.macstyle = 2
	else:
		font.macstyle = 0

def printInfo(font):
	print('font.familyname: ' + font.familyname)
	#print('font.fondname: ' + font.fondname)
	print('font.fontname: ' + font.fontname)
	print('font.fullname: ' + font.fullname)
	sfnt_names = list(font.sfnt_names)
	for i in range(len(sfnt_names)):
		print(sfnt_names[i])

def getStyleNameFromFname(fname, fileBaseName):
	fname = os.path.splitext(fname)[0]
	styleName = fname.replace(fileBaseName, '').replace('-', '').replace('Italic', ' Italic ').replace('italic', ' italic ').replace('  ', ' ').strip()
	if styleName == '':
		styleName = 'Regular'
	return styleName

def getStyleNameFromFname2(fname, fileBaseName): # even more hacks
	if not fileBaseName:
		return 'Regular'
	fname = os.path.splitext(fname)[0]
	styleName = fname.replace(fileBaseName, '').replace('-', '')
	# print(styleName)
	tmp = ''
	for c in styleName:
		if c.isupper():
			tmp += ' '
		tmp += c
	styleName = tmp.replace('S C', 'SC').replace('O S F', 'OSF').replace('Semi Bold', 'SemiBold').replace('  ', ' ').strip()

	# deal with abbr like Med, Ital
	if 'Italic' not in styleName:
		if 'Itali' in styleName:
			styleName = styleName.replace('Itali', 'Italic')
		elif 'Ital' in styleName:
			styleName = styleName.replace('Ital', 'Italic')
		elif styleName.endswith('It'):
			styleName = styleName[:-2] + ' Italic'
	if 'Medium' not in styleName:
		if 'Med' in styleName:
			styleName = styleName.replace('Med', 'Medium')

	# deal with ExtraLight being split into Extra Light, and the like
	if 'ExtraLight' in fname:
		styleName = styleName.replace('Extra Light', 'ExtraLight')
	if 'UltraLight' in fname:
		styleName = styleName.replace('Ultra Light', 'UltraLight')
	if 'ExtraBold' in fname:
		styleName = styleName.replace('Extra Bold', 'ExtraBold')
	if 'SemiBold' in fname:
		styleName = styleName.replace('Semi Bold', 'SemiBold')
	if 'DemiBold' in fname:
		styleName = styleName.replace('Demi Bold', 'DemiBold')
	if 'SmB' in fname:
		styleName = styleName.replace('Sm B', 'SmB')
	if 'XtraB' in fname:
		styleName = styleName.replace('Xtra B', 'XtraB')
	if 'OSF' in fname:
		styleName = styleName.replace('O S F', 'OSF')
	if 'OsF' in fname:
		styleName = styleName.replace('Os F', 'OsF')

	styleName = styleName.replace('  ', ' ').strip()

	if not styleName:
		styleName = 'Regular'
	return styleName

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

def fontSaveGen(font, outPath):
	try:
		if outPath.endswith('.sfd'):
			font.save(outPath)
		else:
			font.generate(outPath)
	except:
		print(outPath)
		return 1
	return 0

def doStuff2():
	global inputList, outputFmt, outputDir, autoDetectAll

	print(' ')
	print("%s v%s by %s" % (programName, version, author))

	if autoDetectAll:
		commonString = ''
		for item in inputList:
			bareName = os.path.splitext(os.path.split(item[0])[1])[0]
			if not commonString:
				commonString = bareName
			elif commonString not in bareName:
				tmp = ''
				maxLength = len(commonString)
				if len(bareName) < maxLength:
					maxLength = len(bareName)
				for i in range(maxLength):
					if commonString[i] == bareName[i]:
						tmp += commonString[i]
					else:
						break
				commonString = tmp

		commonString_stripped = commonString.replace('-', '').strip()

		if commonString_stripped:
			print('Found the longest common string in input filenames: "%s".' % commonString)			
			print('Chose "%s" as font family name and base filename.' % commonString_stripped)

			newInputList = []
			fileBaseName = commonString_stripped
			familyName = commonString_stripped
			for item in inputList:
				fileName = item[0]
				tmp = (fileName, fileBaseName, familyName)
				newInputList.append(tmp)
			inputList = newInputList
		else:
			print('Couldn\'t found any common string in input filenames. Please manually specify font family name and base filename.')
			print('Font family name:'),
			familyName = str(raw_input())
			print('Base filename:'),
			fileBaseName = str(raw_input())

			newInputList = []
			fileBaseName = commonString_stripped
			familyName = commonString_stripped
			for item in inputList:
				fileName = item[0]
				tmp = (fileName, fileBaseName, familyName)
				newInputList.append(tmp)
			inputList = newInputList

	for item in inputList:
		fileName = item[0]
		fileBaseName = item[1]
		familyName = item[2]

		print('\nProcessing file: %s' % fileName)
		if not os.path.isfile(fileName):
			print('Couldn\'t find the file %s' % fileName)
			continue
		folder, fname = os.path.split(fileName)

		if not familyName:
			if fileBaseName:
				# print('It reached here')
				familyName = fileBaseName
			else: # auto-detect
				bareName = os.path.splitext(fname)[0]
				fileBaseName = bareName.split('-')[0]
				familyName = fileBaseName

		styleName = getStyleNameFromFname2(fname, fileBaseName)
		print('familyName = "%s"' % familyName)
		print('styleName = "%s"' % styleName)

		font = fontforge.open(fileName)
		fixFontName(font, familyName, styleName)
		fixFontWeight(font, styleName)
		fixFontMisc(font, styleName)

		if not outputFmt:
			ext = os.path.splitext(fname)[1]
			if ext == '.sfd' or ext == '.otf' or ext == '.ttf':
				fontSaveGen(font, os.path.join(outputDir, os.path.splitext(fname)[0] + ext))
			else:
				fontSaveGen(font, os.path.join(outputDir, os.path.splitext(fname)[0] + '.otf'))
		else:
			for fmt in outputFmt:
				fontSaveGen(font, os.path.join(outputDir, os.path.splitext(fname)[0] + '.' + fmt))

		font.close()

	print('\nAll done.')

initStuff()
parseParams()
checkSanity()
doStuff2()