#!/usr/bin/python

inputPrehashedList = '/media/yumi/zZzZzZ/backup/LinuxMint/apt/prehash.txt'
prehashedList = []
refDir = ["/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives1", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/archives2", "/media/yumi/zZzZzZ/backup/LinuxMint/apt/dump"]
python2 = False

def hashFile(fileName):
	import os, sys, hashlib, zlib

	crc32 = 0
	sha256 = hashlib.sha256()
	blockSize = 2 * 1024 * 1024

	try:
		fd = open(fileName, 'rb')
		while True:
			buffer = fd.read(blockSize)
			if len(buffer) == 0: # EOF or file empty. return hashes
				fd.close()
				if python2 and crc32 < 0:
					crc32 += 2 ** 32
				return '%08X' % crc32, sha256.hexdigest().upper(), False
			crc32 = zlib.crc32(buffer, crc32)
			sha256.update(buffer)

	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		return '%08X' % 0, hashlib.sha256().hexdigest().upper(), error

def hashRefDir():
	import os, sys
	global refDir, prehashedList

	print('Scanning reference dir(s)...')
	count = 0
	for dname in refDir:
		for (dirpath, dirnames, filenames) in os.walk(dname):
			for fname in filenames:
				if fname.endswith(".deb"):
					fullName = os.path.join(dirpath, fname)
					crc32, sha256, error = hashFile(fullName)
					prehashedList.append((fullName, sha256))
					count += 1
	print('Got %d files in %d reference dir(s).' % (count, len(refDir)))

def writeListToFile():
	import os, sys
	f = open(inputPrehashedList, 'w')
	for entry in prehashedList:
		fname, sha256 = entry
		f.write(fname + '\n' + sha256 + '\n')
	f.flush()
	f.close()

hashRefDir()
writeListToFile()