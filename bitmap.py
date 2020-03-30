#!/usr/bin/env python3
import colored_traceback.auto
from tqdm import tqdm
import textwrap

from kellog import debug, info, warning, error

from image import Image

# ==================================================================================================
class Bitmap():
	# ----------------------------------------------------------------------------------------------
	def __init__(self, filePath, offset):
		self.filePath = filePath
		self.offset = offset
		self.images = []

		self.read_header()

	# ----------------------------------------------------------------------------------------------
	def read_header(self):
		with open(self.filePath, "rb") as f:
			f.seek(self.offset)
			self.filename = f.read(65).rstrip(b"\x00").decode("ascii")
			self.comment = f.read(51).rstrip(b"\x00").decode("ascii")
			self.width = int.from_bytes(f.read(4), byteorder="little")
			self.height = int.from_bytes(f.read(4), byteorder="little")
			self.numImages = int.from_bytes(f.read(4), byteorder="little")
			self.startIndex = int.from_bytes(f.read(4), byteorder="little")
			self.endIndex = int.from_bytes(f.read(4), byteorder="little")

			f.seek(64, 1)
			self.offset = f.tell()

	# ----------------------------------------------------------------------------------------------
	def __repr__(self):
		return f"<{__class__.__name__}: {self.filename}>"

	# ----------------------------------------------------------------------------------------------
	def __str__(self):
		return textwrap.dedent(f"""
		{self.filename}
		  Comment: {self.comment}
		  Dimensions: {self.width}x{self.height}
		  Contains {self.numImages} images ({self.startIndex} to {self.endIndex})
		""").strip()

	# ----------------------------------------------------------------------------------------------
	def read_images(self, offset, includeAlpha):
		self.offset = offset
		for i, record in enumerate(tqdm(range(self.numImages))):
			image = Image(self.filePath, self.offset, includeAlpha, i)
			if image and record != 0: # First one is always a dummy record
				self.images.append(image)
			self.offset = image.offset
