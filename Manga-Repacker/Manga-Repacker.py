#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, re, uuid, io, urllib, uuid, shutil
from PIL import Image
from io import BytesIO

plugin_name = 'Manga-Repacker'
appFolder = os.path.dirname(os.path.abspath(__file__))

sevenzipPath = os.path.join(appFolder, '7z.exe')
if sys.platform != 'win32':
	sevenzipPath = '7z'

os.chdir(appFolder)

def processFolder(folderPath):
	input_total_size = 0
	output_total_size = 0
	total_space_saved = 0

	total_image_count = 0
	compressed_image_count = 0
	downscaled_image_count = 0

	print("Processing folder %s..." % folderPath)

	for (dirpath, dirnames, filenames) in os.walk(folderPath):
		for fname in sorted(filenames):
			print(fname)
			# Only continue if it's a known static image
			# Well, at least don't touch GIF (may have animation) or whatever uncommon formats
			dummy, ext = os.path.splitext(fname)
			if ext.upper() not in ['.BMP', '.PNG', '.JPEG', '.JPG', '.WEBP']:
				print('Not BMP, PNG, JPEG, or WEBP. Skipped.')
				continue

			imagePath = os.path.join(dirpath, fname)

			oldSize = os.path.getsize(imagePath)
			input_total_size += oldSize
			total_image_count += 1

			changed, downscaled, newSize = processFile(imagePath)

			if changed:
				compressed_image_count += 1
				total_space_saved += oldSize - newSize
				output_total_size += newSize
				if downscaled:
					downscaled_image_count += 1
			else:
				output_total_size += oldSize

	print("\nProcessed %d files. Input size: %s." % (total_image_count, byteToHumanSize(input_total_size)))
	print("Compressed: %d. Downscaled: %d." % (compressed_image_count, downscaled_image_count))
	print("Output size: %s. Saved %s (%d%%)." % (byteToHumanSize(output_total_size), byteToHumanSize(total_space_saved), 100.0 * total_space_saved / input_total_size))


# input: path to image file
# output: (changed?, downscaled?, newSize)
def processFile(imagePath, silent=True):
	downscale_image_larger_than_xxx = True
	large_image_px = 1600 # image is considered large if any of its dimensions is larger than this
	downscale_to_px = 1600

	if not silent:
		print('\nProcessing image: %s' % imagePath)

	changed = False
	downscaled = False
	newSize = 0

	# read image
	try:
		im =  Image.open(imagePath)
	except Exception as e:
		if not silent:
			print('Error: %r' % e)
			print('Skipped.')
		return (changed, downscaled, newSize)

	# show original info
	original_size = os.path.getsize(imagePath)
	original_format = im.format
	if not silent:
		print('Input size: %d (bytes)' % original_size)
		print('Input format: %s' % im.format)
		print('Input dimensions: %dx%dpx' % (im.size))

	# Only continue if it's BMP, PNG, and JPEG
	# Well, at least don't touch GIF (may have animation) or whatever uncommon formats
	if original_format not in ['BMP', 'PNG', 'JPEG', 'WEBP']:
		if not silent:
			print('Not BMP, PNG, JPEG, or WEBP. Skipped.')
		return (changed, downscaled, newSize)

	downscaled = False
	if downscale_image_larger_than_xxx:
		im_width, im_height = im.size
		im_new_width, im_new_height = im.size

		if im_width > large_image_px or im_height > large_image_px:
			if im_width > im_height:
				im_new_width = downscale_to_px
				im_new_height = int(1.0 * downscale_to_px / (1.0 * im_width / im_height))
			else:
				im_new_height = downscale_to_px
				im_new_width = int(1.0 * downscale_to_px * (1.0 * im_width / im_height))

		if im_new_width < im_width:
			try: # the best-quality resampler PIL supports is LANCZOS. It was named ANTIALIAS in old version
				resampler = Image.LANCZOS
			except:
				resampler = Image.ANTIALIAS
			im = im.resize((im_new_width, im_new_height), resampler)
			if not silent:
				print('Downscaled image to %dx%dpx' % (im_new_width, im_new_height))
			downscaled = True
			# print(im.size)

	# Test a few encodings to get the smallest size.
	# - PNG - best for texts and sharp patterns (smaller than jpg and lossless quality). Quite big for common photos.
	# - JPG - good quality/size ratio for photos. Bad for texts. We go with 90% quality.
	# - WEBP - new format, can be 25-35% smaller than JPG at the same quality
	# Progressive JPGs are almost always smaller than baseline (normal) JPGs
	# The different is not large, but there's no drawback except negligible performance loss
	# Only use lossy compression if it saves more than 10%
	# Note that mode P can't be saved to jpg directly, convert it to RGB first
	imgOut1 = BytesIO()
	# JPEG output
	# im.convert("RGB").save(imgOut1, 'JPEG', quality=90, optimize=True, progressive=True)
	# WEBP output internally converts mode P to RGB (but faster), so no need to convert first
	im.save(imgOut1, 'WEBP', quality=90, method=5)
	lossy_out_size = len(imgOut1.getvalue())
	lossy_out_format = 'WEBP'
	if not silent:
		print('Output lossy size: %d' % lossy_out_size)

	output_format = ''
	output_binary = BytesIO()
	output_size = original_size
	if (original_format in ['PNG', 'BMP']): # lossless source
		# to save time, only do lossless compression if the source is lossless
		imgOut2 = BytesIO()
		# im.save(imgOut2, 'PNG', optimize=True)
		# switch to lossless webp because it saves much more space
		im.save(imgOut2, 'WEBP', lossless=True)
		lossless_out_size = len(imgOut2.getvalue())
		lossless_out_format = 'WEBP'
		if not silent:
			print('Output lossless size: %d' % lossless_out_size)

		# go with lossy if it saves at least 10%, and significantly more than lossless does
		if (lossy_out_size <= 0.9*original_size) and (lossy_out_size <= 0.9*lossless_out_size):
			output_format = lossy_out_format
			output_binary = imgOut1
			newSize = lossy_out_size

		# otherwise, go with png if it saves something
		elif (lossless_out_size < original_size):
			output_format = lossless_out_format
			output_binary = imgOut2
			newSize = lossless_out_size

	else: # source is lossy
		# go with lossy if it saves at least 10%
		if (lossy_out_size <= 0.9*original_size):
			output_format = lossy_out_format
			output_binary = imgOut1
			newSize = lossy_out_size

	im.close();

	if output_format: # only save output if a format is selected above
		changed = True

		space_saved = (original_size) - newSize
		if not silent:
			print('Selected format: %s' % output_format)
			print('Saved space: %d (%d%%)' % (space_saved, 100.0 * space_saved / original_size))
		# total_space_saved += space_saved
		# compressed_image_count += 1
		# if downscaled:
		# 	downscaled_image_count += 1

		# write output, delete the original file
		os.remove(imagePath)

		bareName, ext = os.path.splitext(imagePath)
		new_ext = '.' + output_format.lower()
		outputName = bareName + new_ext

		# Write the stuff
		with open(outputName, "wb") as f:
			f.write(output_binary.getbuffer())
	else:
		if not silent:
			print('No significant space saves. No change.')

	return (changed, downscaled, newSize)


def byteToHumanSize(size):
	if size >= 1000 * 1024 * 1024:
		return '%0.3f GiB' % (size / (1024 ** 3))
	elif size >= 1000 * 1024:
		return '%0.3f MiB' % (size / 1024 ** 2)
	elif size >= 1000:
		return '%0.3f KiB' % (size / 1024)
	else:
		return '%s bytes' % size


# executes given task and return console output, return code and error message if any
def executeTask(params, taskName = ''):
	import subprocess, sys
	if taskName != '':
		printAndLog('Executing task "%s"...' % taskName)

	execOutput = ''
	returnCode = 0
	error = False
	try:
		execOutput = subprocess.check_output(params)
	except subprocess.CalledProcessError as e:
		execOutput = e.output
		returnCode = e.returncode
		error = True
	if sys.stdout.encoding != None: # It's None when debugging in Sublime Text
		try:
			execOutput = execOutput.decode(sys.stdout.encoding)
		except:
			pass

	return execOutput, returnCode, error


def packToArchive(filenames, archive):
	zparams = [sevenzipPath, 'a', '-aoa', '-tzip']
	zoutput = archive

	# don't need to check if fname is valid. 7z will just ignore invalid inputs
	zparams.append(zoutput)
	for fname in filenames:
		zparams.append(fname)
	# print(zparams)

	# delete existing output file (if any) to prevent 7z from adding files to it
	try:
		os.remove(zoutput)
	except:
		pass

	print('Creating archive "%s" from [ %s ]' % (zoutput, ', '.join(filenames)))
	executeTask(zparams)


def extractArchive(filePath, outputFolder):
	zparams = [sevenzipPath, 'x', filePath, "-o%s" % outputFolder, '-aoa']
	# print(zparams)

	print('Extracting archive "%s" to "%s"' % (filePath, outputFolder))
	executeTask(zparams)


def getFolderContents(folderPath):
	listOfFiles = []
	for (dirpath, dirnames, filenames) in os.walk(folderPath):
		listOfFiles = [os.path.join(dirpath, file) for file in filenames + dirnames]
		break
	return listOfFiles


def main():
	inputCount = len(sys.argv) - 1
	print("Got %d inputs from paramenters." % inputCount)

	for inFile in sys.argv[1:]:
		if os.path.exists(inFile):
			doStuff(inFile)
		else:
			print("File not found: %s" % inFile)

def doStuff(inFile):
	# processFolder(u"E:\\Downloads\\Machimaho - I Messed Up and Made the Wrong Person Into a Magical Girl! (Digital) (danke-Empire)\\1")
	# packToArchive(["E:\\Downloads\\Machimaho - I Messed Up and Made the Wrong Person Into a Magical Girl! (Digital) (danke-Empire)\\1\\*"], 'r:\\a.cbz')
	# extractArchive(r"R:\a.cbz", 'R:\\t')
	# print(getFolderContents(u"E:\\Downloads\\Machimaho - I Messed Up and Made the Wrong Person Into a Magical Girl! (Digital) (danke-Empire)\\1"))
	# return

	# inFile = "E:\\Downloads\\Machimaho - I Messed Up and Made the Wrong Person Into a Magical Girl! (Digital) (danke-Empire)\\Machimaho - I Messed Up and Made the Wrong Person Into a Magical Girl! v01 (2018) (Digital) (danke-Empire).cbz"

	isFile = os.path.isfile(inFile)
	suffix = ' (repacked).cbz'

	# if inFile is a folder, copy it instead of extracting

	if isFile:
		outFile = os.path.splitext(inFile)[0] + suffix
	else:
		outFile = inFile + suffix

	tmpDir = str(uuid.uuid4())

	if isFile:
		extractArchive(inFile, tmpDir)
	else:
		print('Copying input folder "%s" to "%s"' % (inFile, tmpDir))
		shutil.copytree(inFile, tmpDir)

	processFolder(tmpDir)
	packToArchive([os.path.join(tmpDir, '*')], outFile)
	print("Removing temp dir...")
	shutil.rmtree(tmpDir)

if __name__ == "__main__":
	sys.exit(main())
