#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, re, uuid, io, urllib, uuid, shutil
from PIL import Image
from io import BytesIO

plugin_name = 'Manga-Repacker'
appFolder = os.path.dirname(os.path.abspath(__file__))

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
			# Only continue if it's BMP, PNG, and JPEG
			# Well, at least don't touch GIF (may have animation) or whatever uncommon formats
			dummy, ext = os.path.splitext(fname)
			if ext.upper() not in ['.BMP', '.PNG', '.JPEG', '.JPG']:
				print('Not BMP, PNG, or JPEG. Skipped.')
				continue

			imagePath = os.path.join(dirpath, fname)

			oldSize = os.path.getsize(imagePath)
			input_total_size += oldSize
			total_image_count += 1

			changed, downscaled, newSize = processFile(imagePath, True)

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
def processFile(imagePath, silent):
	skip_png_compression_for_png_inputs = True
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
	if original_format not in ['BMP', 'PNG', 'JPEG']:
		if not silent:
			print('Not BMP, PNG, or JPEG. Skipped.')
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

	# Try a few encoding to get the smallest size.
	# - PNG - best for texts and sharp patterns (smaller than jpg and lossless quality). Quite big for common photos.
	# - JPG - good quality/size ratio for photos. Bad for texts. We go with 90% quality.
	# Progressive JPGs are almost always smaller than baseline (normal) JPGs
	# The different is not large, but there's no drawback except negligible performance loss
	# Only use lossy compression if it saves more than 10%
	# Note that mode P can't be saved to jpg directly, convert it to RGB first
	imgOut1 = BytesIO()
	im.convert("RGB").save(imgOut1, 'JPEG', quality=90, optimize=True, progressive=True)
	jpg_out_size = len(imgOut1.getvalue())
	if not silent:
		print('Output JPEG size: %d' % jpg_out_size)

	output_format = '' # empty = do nothing
	output_binary = ''
	if (original_format in ['PNG', 'BMP']): # lossless source
		# to save time, only do lossless compression if the source is lossless
		# to speed up even more, skip png compression for png inputs, as it usually doesn't help
		if downscaled or original_format != 'PNG' or (original_format == 'PNG' and not skip_png_compression_for_png_inputs):
			imgOut2 = BytesIO()
			im.save(imgOut2, 'PNG', optimize=True)
			png_out_size = len(imgOut2.getvalue())
			if not silent:
				print('Output PNG size: %d' % png_out_size)
			# go with jpg if it saves at least 10%, and significantly more than png does
			if (jpg_out_size <= 0.9*original_size) and (jpg_out_size <= 0.9*png_out_size):
				output_format = 'JPEG'
				output_binary = imgOut1.getvalue()
			# otherwise, go with png if it saves something
			elif (png_out_size < original_size):
				output_format = 'PNG'
				output_binary = imgOut2.getvalue()
		else:
			# go with jpg if it saves at least 10%
			if (jpg_out_size <= 0.9*original_size):
				output_format = 'JPEG'
				output_binary = imgOut1.getvalue()
	else: # source is lossy
			# go with jpg if it saves at least 10%
			if (jpg_out_size <= 0.9*original_size):
				output_format = 'JPEG'
				output_binary = imgOut1.getvalue()

	im.close();

	if output_format:
		changed = True
		newSize = len(output_binary)

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
		new_ext = '.jpg'
		if output_format == 'PNG':
			new_ext = '.png'
		outputName = bareName + new_ext

		# Write the stuff
		with open(outputName, "wb") as f:
			f.write(imgOut1.getbuffer())
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
		execOutput = execOutput.decode(sys.stdout.encoding)

	return execOutput, returnCode, error


def packToArchive(filenames, archive):
	sevenzipPath = os.path.join(appFolder, '7z.exe')
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
	sevenzipPath = os.path.join(appFolder, '7z.exe')
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
	outFile = os.path.splitext(inFile)[0] + ' (repacked).cbz'

	tmpDir = str(uuid.uuid4())
	extractArchive(inFile, tmpDir)
	processFolder(tmpDir)
	packToArchive([os.path.join(tmpDir, '*')], outFile)
	print("Removing temp dir...")
	shutil.rmtree(tmpDir)

if __name__ == "__main__":
	sys.exit(main())
