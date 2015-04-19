#!/usr/bin/python
# encoding: utf-8

import fontforge, os, random, sys

programName = "Small Caps, OSF, etc. styles generator"
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

def getGlyphByName(font, glyphname):
	for glyph in font.glyphs():
		if (glyph.glyphname == glyphname):
			return glyph
	return None

def getGlyphByName2(font, glyphname):
	# font[glyphname], which is much faster, might return something else if the glyph with that exact name is not found
	try:
		return font[glyphname]
	except:
		return None

def countGlyphWithName(font, glyphname):
	count = 0
	for glyph in font.glyphs():
		if glyph.glyphname == glyphname:
			count = count + 1
	return count

def getLookupTableName(font, feature):
	everything = font.gsub_lookups
	for lookup in everything:
		if (lookup.startswith("'%s'" % feature)):
			return lookup + ' subtable'
	return ''

def checkFeature(font, feature):
	everything = font.gsub_lookups
	for lookup in everything:
		if lookup.startswith("'%s'" % feature):
			return True
	return False

def getNameRecordValue(font, nameRecord):
	for sfnt_name in font.sfnt_names:
		if sfnt_name[1] == nameRecord:
			return sfnt_name[2]
	return None

def getFamilyName(font):
	# 'Preferred Family' should be the correct family name
	# 'Family' might be really the family name, or it plus style link group, or something else (broken case)
	# font.familyname might be the correct family name, too
	familyName_old = getNameRecordValue(font, 'Family')
	preferredFamily = getNameRecordValue(font, 'Preferred Family')
	if preferredFamily:
		familyName_old = preferredFamily
	if not familyName_old:
		familyName_old = font.familyname
	return familyName_old

def replacer(text, familyName_old, familyName_new, dontStripSpace=False):
	if not dontStripSpace:
		familyName_new_strip = familyName_new.replace(' ', '')
	else:
		familyName_new_strip = familyName_new
	if familyName_old.replace(' ', '') in text:
		text = text.replace(familyName_old.replace(' ', ''), familyName_new_strip)
	elif familyName_old in text:
		text = text.replace(familyName_old, familyName_new)
	elif text.lower().startswith(familyName_old.replace(' ', '').lower()): # fix Palatino nova W1G / PalatinoNovaW1G (different case, font naming bug)
		text = familyName_new_strip + text[len(familyName_old.replace(' ', '')):]
	elif text.lower().startswith(familyName_old.lower()):
		text = familyName_new + text[len(familyName_old):]
	return text

def renameFont_suffix(font, suffix, forceInsertSpace=False, familyName=None):
	def replacer2(text, dontStripSpace=forceInsertSpace):
		return replacer(text, familyName_old, familyName_new, dontStripSpace)

	familyName_old = getFamilyName(font)

	if ' ' in familyName_old or forceInsertSpace:
		familyName_new = familyName_old + ' ' + suffix
	else:
		familyName_new = familyName_old + suffix

	sfnt_names = list(font.sfnt_names) # convert tuple <-> list huehuehue
	for i in range(len(sfnt_names)):
		sfnt_names[i] = list(sfnt_names[i])
		tmp = sfnt_names[i][1]
		if tmp == 'Family' or tmp == 'UniqueID' or tmp == 'Fullname' or tmp == 'Preferred Family' or tmp == 'Compatible Full':
			sfnt_names[i][2] = replacer2(sfnt_names[i][2])
		if tmp == 'PostScriptName':
			sfnt_names[i][2] = replacer2(sfnt_names[i][2], dontStripSpace=False)
		sfnt_names[i] = tuple(sfnt_names[i])
	font.sfnt_names = tuple(sfnt_names)

	if font.familyname != getNameRecordValue(font, 'Family'): # fixed for whatever linking between them Fontforge is keeping
		font.familyname = replacer2(font.familyname)
	if font.fontname != getNameRecordValue(font, 'PostScriptName'):
		font.fontname = replacer2(font.fontname, dontStripSpace=False)
	if font.fullname !=getNameRecordValue(font, 'Fullname'):
		font.fullname = replacer2(font.fullname)
	if font.fondname != None:
		font.fondname = replacer2(font.fondname) # should be independent

def renameFont_prefix(font, prefix, forceInsertSpace=False, familyName=None):
	def replacer2(text):
		return replacer(text, familyName_old, familyName_new)

	familyName_old = getFamilyName(font)

	if (' ' in familyName_old):
		familyName_new = prefix + ' ' + familyName_old
	else:
		familyName_new = prefix + familyName_old

	sfnt_names = list(font.sfnt_names) # convert tuple <-> list huehuehue
	for i in range(len(sfnt_names)):
		sfnt_names[i] = list(sfnt_names[i])
		tmp = sfnt_names[i][1]
		if tmp == 'Family' or tmp == 'UniqueID' or tmp == 'Fullname' or tmp == 'PostScriptName' or tmp == 'Preferred Family' or tmp == 'Compatible Full':
			sfnt_names[i][2] = replacer2(sfnt_names[i][2])
		sfnt_names[i] = tuple(sfnt_names[i])
	font.sfnt_names = tuple(sfnt_names)

	if font.familyname != getNameRecordValue(font, 'Family'): # fixed for whatever linking between them Fontforge is keeping
		font.familyname = replacer2(font.familyname)
	if font.fontname != getNameRecordValue(font, 'PostScriptName'):
		font.fontname = replacer2(font.fontname)
	if font.fullname != getNameRecordValue(font, 'Fullname'):
		font.fullname = replacer2(font.fullname)
	if font.fondname:
		font.fondname = replacer2(font.fondname) # should be independent

def substituteGlyphsWithSuffix(font, suffix):
	cutoff = - len(suffix)
	for glyph in font.glyphs():
		if glyph.glyphname.endswith(suffix):
			glyph_re = getGlyphByName(font, glyph.glyphname[:cutoff])
			if glyph_re: # TODO: handle cases like in applyFeatureToGlyph
				glyph.unicode, glyph_re.unicode = glyph_re.unicode, glyph_re.unicode
	return None

def applyFeatureToGlyph(font, glyph, feature, forceRe=False, copyGlyph=False, overWr=False, copyBehavior=2):
	# glyph a: (("'case' Case-Sensitive Forms in Latin lookup 20 subtable", 'Substitution', 'A'), ("'smcp' Lowercase to Small Capitals in Latin lookup 18 subtable", 'Substitution', 'a.sc'), ("'ordn' Ordinals in Latin lookup 17 subtable", 'Substitution', 'ordfeminine'))
	# glyph one: (('Single Substitution lookup 25 subtable', 'Substitution', 'one.denominator'), ("'dnom' Denominators in Latin lookup 16 subtable", 'Substitution', 'one.denominator'), ("'numr' Numerators in Latin lookup 15 subtable", 'Substitution', 'one.numerator'), ("'frac' Diagonal Fractions in Latin lookup 13 subtable", 'Substitution', 'one.numerator'), ("'sinf' Scientific Inferiors in Latin lookup 10 subtable", 'Substitution', 'one.inferior'), ("'sups' Superscript in Latin lookup 9 subtable", 'Substitution', 'onesuperior'), ("'onum' Oldstyle Figures in Latin lookup 7 subtable", 'Substitution', 'one.taboldstyle'), ("'pnum' Proportional Numbers in Latin lookup 6 subtable", 'Substitution', 'one.fitted'))
	beVerbose = False
	try:
		replacement = None
		replacements = glyph.getPosSub('*')
		for re in replacements:
			if (re[0].startswith("'%s'" % feature)):
				replacement = re
				break
	except:
		return 2 # feature not available

	if replacement:
		# OK, sometimes the replacement is not available in the font
		glyph_re = getGlyphByName(font, replacement[2])
		if not glyph_re: # retry with font[glyphname]. Maybe a bit risky
			glyph_re = getGlyphByName2(font, replacement[2])
		if not glyph_re: # give up
			return 2

		if beVerbose: print(glyph_re)
		if glyph.unicode == -1 or glyph_re.unicode == glyph.unicode:
			return 0 # nothing to do
		elif glyph_re.unicode == -1 or forceRe == True:
			# Only give its unicode point to its substitution if the later hasn't been assigned to something else. 
			# This is to fix issue with s.sc in SinaNova but will cause issues with Elysium/SC or Aldus/SC as smallcaps are all mapped
			# use forceRe (unsafe) if you want, or better, copy/overwrite (when implemented)
			glyph_re.unicode = glyph.unicode
			glyph.unicode = -1
			return 0 # all OK

		elif copyGlyph == True: # copying is believed to be safe # TODO: copy any pos sub data associated with the glyph
			if beVerbose: print("Substituting glyph by copying...")

			# generate a new unique name
			copynum = 0
			glyph_newName = '%s.copy%d' % (glyph_re.glyphname, copynum)
			while countGlyphWithName(font, glyph_newName) != 0:
				copynum = copynum + 1
				glyph_newName = '%s.copy%d' % (glyph_re.glyphname, copynum)

			# create a new glyph with that name
			font.createChar(-1, glyph_newName)

			# copy & paste glyph_re into glyph_newName
			font.selection.none()
			font.selection.select(glyph_re)
			font.copy()
			font.selection.none()
			font.selection.select(glyph_newName)
			font.paste()
			
			# set unicode point
			glyph_copy = font[glyph_newName]
			glyph_copy.unicode = glyph.unicode
			glyph.unicode = -1

			# add pos sub data to glyph glyph_copy with addPosSub 
			# kerning data needs to be modified. Will do later
			# glyph_copy.removePosSub('*') # it should have no pos sub data at all
			# posSubs = glyph.getPosSub('*')

			if copyBehavior == 2: # swap the unicode points of the original glyph and the copy
				glyph_copy.unicode, glyph_re.unicode = glyph_re.unicode, glyph_copy.unicode

			return 0

		elif overWr == True: # overwriting is believed to be safe # TODO: copy any pos sub data associated with the glyph
			# print('Substituting glyph by overwriting...')
			font.selection.none()
			font.selection.select(glyph_re)
			font.copy()
			font.selection.none()
			font.selection.select(glyph)
			font.paste()

			if copyBehavior == 2: # swap the unicode points of the original glyph and the copy
				glyph.unicode, glyph_re.unicode = glyph_re.unicode, glyph_re.unicode
			return 0
		else:
			return 1 # can't replace. copying not allowed
	else:
		return 2 # feature not available for this glyph

def turnonFeature(sina, enableSmallCaps=False, enableStyleAlt=False, setFigure=0, setNumber=0, forceRe=False, copyGlyph=False, overWr=False, allSmallCaps=False):
	# figure 0 = don't change, 1 = lining, 2 = old style
	# number 0 = don't change, 1 = proportional, 2 = tabular

	hasFeature_SC = checkFeature(sina, 'smcp')
	hasFeature_C2SC = checkFeature(sina, 'c2sc')
	hasFeature_OSF = checkFeature(sina, 'onum')
	hasFeature_LF = checkFeature(sina, 'lnum')
	hasFeature_ProNum = checkFeature(sina, 'pnum')
	hasFeature_TabNum = checkFeature(sina, 'tnum')
	hasFeature_StyleAlt = checkFeature(sina, 'salt')

	if allSmallCaps and not hasFeature_C2SC:
		print('Capital to Smallcap feature unavailable.')		

	if enableSmallCaps:
		if hasFeature_SC:
			# total = 0
			# replaced = 0
			for glyph in sina.glyphs():
				# if glyph.glyphname == 'dotlessi': continue
				# attempt to use sc, and fall back to c2sc for numbers
				# if c2sc/smcp for numbers is unavailable, users can use OSF instead
				# some fonts like ElysiumStd actually use OSF for SC
				succ = applyFeatureToGlyph(sina, glyph, 'smcp', forceRe, copyGlyph, overWr)
				if succ == 2 and hasFeature_C2SC and ((glyph.unicode >= 48 and glyph.unicode <= 57) or allSmallCaps):
					succ2 = applyFeatureToGlyph(sina, glyph, 'c2sc', forceRe, copyGlyph, overWr)
				elif succ == 1:
					# succ3 = applyFeatureToGlyph(sina, glyph, 'smcp', forceRe, copyGlyph=False, overWr=True) 
					succ3 = applyFeatureToGlyph(sina, glyph, 'smcp', forceRe, copyGlyph=True, overWr=False) 
				# if glyph.glyphname == 'i':
				# 	print('succ = %d' % succ)
				# if succ == 0:
				# 	replaced = replaced + 1
				# if succ == 0 or succ == 1:
				# 	total = total + 1
			# print('Total: %d. Replaced: %d.' % (total, replaced))
			# glyph = getGlyphByName(sina, 'a')
			# print(lookupName_SC)
			# print(glyph.getPosSub('*'))
		else:
			print('Small Capitals feature unavailable.')

	if enableStyleAlt:
		if hasFeature_StyleAlt:
			for glyph in sina.glyphs():
				succ = applyFeatureToGlyph(sina, glyph, 'salt', forceRe, copyGlyph, overWr)
		else:
			print('Stylistic Alternatives feature unavailable.')

	if setFigure == 1:
		if hasFeature_LF:
			for glyph in sina.glyphs():
				succ = applyFeatureToGlyph(sina, glyph, 'lnum', forceRe, copyGlyph, overWr)
		else:
			print('Lining Figures feature unavailable.')

	if setFigure == 2:
		if hasFeature_OSF:
			for glyph in sina.glyphs():
				succ = applyFeatureToGlyph(sina, glyph, 'onum', forceRe, copyGlyph, overWr)
		else:
			print('Old Style Figures feature unavailable.')

	if setNumber == 1:
		if hasFeature_ProNum:
			for glyph in sina.glyphs():
				succ = applyFeatureToGlyph(sina, glyph, 'pnum', forceRe, copyGlyph, overWr)
		else:
			print('Proportional Numbers feature unavailable.')

	if setNumber == 2:
		if hasFeature_TabNum:
			for glyph in sina.glyphs():
				succ = applyFeatureToGlyph(sina, glyph, 'tnum', forceRe, copyGlyph, overWr)
		else:
			print('Tabular Numbers feature unavailable.')

def fixFontMisc(font):
	os2_version = font.os2_version
	if os2_version < 2: # windows will reject otf cff font with os2 version 1
		font.os2_version = 3

def makeFontFiles(path):
	sina = fontforge.open(path)
	sina.generate(os.path.splitext(path)[0] + '.ttf')
	sina.generate(os.path.splitext(path)[0] + '.otf')
	sina.close()

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

def doStuff():
	global inputList, outputFmt, outputDir

	print(' ')
	print("%s v%s by %s" % (programName, version, author))

	for item in inputList:
		# print(item)
		fileName = item[0]
		enableSmallCaps = item[1]
		enableStyleAlt = item[2]
		setFigure = item[3]
		setNumber = item[4]
		suffix = item[5]
		substitutingSuffixes = item[6]
		forceInsertSpace = item[7]
		allSmallCaps = item[8]

		print('\nProcessing file: %s' % fileName)
		if not os.path.isfile(fileName):
			print('Couldn\'t find the file %s' % fileName)
			continue
		folder, fname = os.path.split(fileName)

		font = fontforge.open(fileName)

		# now handle suffix in output filename
		familyName_old = getFamilyName(font) # must be before renameFont_suffix because it will change the font name
		if ' ' in familyName_old or forceInsertSpace:
			familyName_new = familyName_old + ' ' + suffix
		else:
			familyName_new = familyName_old + suffix

		outFname, ext = os.path.splitext(fname)
		tmp = replacer(outFname, familyName_old, familyName_new, forceInsertSpace)

		if tmp != outFname: # replacing is successful, well probably. It's fine as long as it's different lol
			outFname = tmp
		elif '-' in outFname:
			elements = outFname.split('-')
			outFname = elements[0] + suffix + '-' + ''.join(elements[1:])
		else:
			if ' ' in outFname or forceInsertSpace:
				outFname = outFname + ' ' + suffix
			else:
				outFname = outFname + suffix

		turnonFeature(font, enableSmallCaps, enableStyleAlt, setFigure, setNumber, allSmallCaps=allSmallCaps)
		if substitutingSuffixes:
			for subSuf in substitutingSuffixes:
				substituteGlyphsWithSuffix(font, subSuf)
		renameFont_suffix(font, suffix, forceInsertSpace)
		fixFontMisc(font)

		if not outputFmt:
			if ext == '.sfd' or ext == '.otf' or ext == '.ttf':
				fontSaveGen(font, os.path.join(outputDir, outFname + ext))
			else:
				fontSaveGen(font, os.path.join(outputDir, outFname + '.otf'))
		else:
			for fmt in outputFmt:
				fontSaveGen(font, os.path.join(outputDir, outFname + '.' + fmt))

		font.close()

	print('\nAll done.')

def parseParams():
	global inputList, outputDir, outputFmt

	enableSmallCaps = False
	allSmallCaps = False
	enableStyleAlt = False
	setFigure = 0
	setNumber = 0
	suffix = 'SC'
	forceInsertSpace = False
	substitutingSuffixes = []

	i = 1
	args = sys.argv
	argsCount = len(args)
	allInputs = False
	while i < argsCount:
		arg = args[i]
		if arg.startswith('-') and not allInputs:
			if arg.startswith('--'):
				arg = arg[2:]
			else:
				arg = arg[1:]
			arg = arg.lower()
			
			if arg == "f" and i < argsCount - 1:
				setFigure = int(args[i+1])
				i += 1
			elif arg == "n" and i < argsCount - 1:
				setNumber = int(args[i+1])
				i += 1
			elif arg == "sf" and i < argsCount - 1:
				suffix = args[i+1]
				i += 1
			elif arg == "o" and i < argsCount - 1:
				outputDir = args[i+1]
				i += 1
			elif arg == "fmt" and i < argsCount - 1:
				fmts = args[i+1].split(',')
				outputFmt = []
				for fmt in fmts:
					outputFmt.append(fmt)
				i += 1
			elif arg == "sub" and i < argsCount - 1:
				sufes = args[i+1].split(',')
				substitutingSuffixes = []
				for suf in sufes:
					substitutingSuffixes.append(suf)
				i += 1
			elif arg == "sp":
				forceInsertSpace = True
			elif arg == "sc":
				enableSmallCaps = True
			elif arg == "sca":
				allSmallCaps = True
			elif arg == 'sa':
				enableStyleAlt = True
		else:
			tmp = (arg, enableSmallCaps, enableStyleAlt, setFigure, setNumber, suffix, substitutingSuffixes, forceInsertSpace, allSmallCaps)
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
	print("Syntax: fontforge -script fontforge.py [options] inputs [[optioms] [inputs]]")
	print(' ')
	print("Options:")
	print("    -sc                   Enable Small Caps feature")
	print("    -sca                  Also enable Small Caps feature for uppercase glyphs")
	print("    -sa                   Enable Stylistic Alternatives feature")
	print('    -f number             Set figures to [1] Lining, [2] Oldstyle, [0] no change')
	print('    -n number             Set number to [1] Proportional, [2] Tabular, [0] no change')
	print('    -sub ".sc,.oldstyle"  Substitute glyphs with specified suffixes with those without')
	print('    -o "output dir"       Set where to save outputs')
	print('    -sf "suffix"          Add suffix to font name')
	print('    -sp                   Force inserting a space between family name and suffix')
	print('    -fmt "otf,ttf,sfd"    Set output formats via file extension')
	print("    -i                    All following paramemters are inputs")
	print(' ')
	print('Note:')
	print('    All switches are optional and, except for -o, take effect on inputs following them.')
	print('    Output directory is <current working directory> by default.')
	print('    Output files, if already existing, will be overwritten without prompt.')
	print('    If not specified, output format is the same as input if it\' either otf, ttf, or sfd; otf otherwise.')
	print('    If not specified, suffix is "SC".')
	print('    A space is inserted between family name and suffix only when family name already has space(s) in it.')
	print('    For examples: Arno Pro SC, SinaNovaSC. Use -sp to force inserting a space if you want.')
	print('    Specific substitution should be used only with fonts with broken substitution tables.')
	print('    Option -sca only has effect when -sc is on.')
	print(' ')
	print("Examples:")
	print('    fontforge -script fontforge.py -fmt "otf,ttf" -f 2 -n 0 -sc -sf "SC" "SinaNova-Regular.sfd"')

initStuff()
parseParams()
checkSanity()
doStuff()