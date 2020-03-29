#!/usr/bin/env python3
import colored_traceback.auto
import textwrap

from kellog import debug, info, warning, error

from bitmap import Bitmap

# ==================================================================================================
class DataFile():
	headerSize = 680
	bitmapRecordSize = 200
	# ----------------------------------------------------------------------------------------------
	def __init__(self, filePath):
		self.filePath = filePath
		self.offset = 0
		self.bitmaps = []

		self.read_header()
		self.read_bitmaps()
		self.offset = self.headerSize + (self.get_max_bitmap_records() * self.bitmapRecordSize)
		self.read_images()

	# ----------------------------------------------------------------------------------------------
	def read_header(self):
		with open(self.filePath, "rb") as f:
			self.fileSize = int.from_bytes(f.read(4), byteorder="little")
			self.version = int.from_bytes(f.read(4), byteorder="little")
			self.unknown1 = int.from_bytes(f.read(4), byteorder="little")
			self.maxImageRecords = int.from_bytes(f.read(4), byteorder="little", signed=True)
			self.numImageRecords = int.from_bytes(f.read(4), byteorder="little", signed=True)
			self.numBitmapRecords = int.from_bytes(f.read(4), byteorder="little", signed=True)
			self.numBitmapRecordsWithoutSystem = int.from_bytes(f.read(4), byteorder="little", signed=True)
			self.totalFilesize = int.from_bytes(f.read(4), byteorder="little")
			self.filesize555 = int.from_bytes(f.read(4), byteorder="little")
			self.filesizeExternal = int.from_bytes(f.read(4), byteorder="little")
			f.seek(self.headerSize)
			self.offset = f.tell()

	# ----------------------------------------------------------------------------------------------
	def __repr__(self):
		return f"<{__class__.__name__}: {self.filePath.name}>"

	# ----------------------------------------------------------------------------------------------
	def __str__(self):
		return textwrap.dedent(f"""
		{self.filePath.name}
		  Version: {self.version}
		  Filesize: {self.fileSize // 1024} KB
		  Contains {self.numBitmapRecords} bitmaps, consisting of {self.numImageRecords} images
		  Image filesize: {self.totalFilesize // 1024} KB ({self.filesize555 // 1024} KB + {self.filesizeExternal // 1024} KB)
		""").strip()

	# ----------------------------------------------------------------------------------------------
	def get_max_bitmap_records(self):
		if self.version == 0xd3:
			return 100 # SG2
		else:
			return 200 # SG3

	# ----------------------------------------------------------------------------------------------
	def read_bitmaps(self):
		with open(self.filePath, "rb") as f:
			f.seek(self.offset)
			for i in range(self.numBitmapRecords):
				bitmap = Bitmap(self.filePath, self.offset)
				self.bitmaps.append(bitmap)
				self.offset = bitmap.offset
			assert(self.bitmaps[-1].endIndex == self.numImageRecords)

	# ----------------------------------------------------------------------------------------------
	def read_images(self):
		for bitmap in self.bitmaps:
			bitmap.read_images(self.offset, self.version >= 0xd6)
			self.offset = bitmap.offset
