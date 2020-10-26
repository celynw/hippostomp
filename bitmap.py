#!/usr/bin/env python3
import colored_traceback.auto
from tqdm import tqdm
import textwrap
from PIL import Image as PILImage
from kellog import debug, info, warning, error

from image import Image, ImageError

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
	def read_images(self, offset, includeAlpha, combine):
		self.offset = offset
		if combine:
			self.images = PILImage.new("RGBA", (self.width, self.height))
		for i, record in enumerate(tqdm(range(self.numImages))):
			image = Image(self.filePath, self.offset, includeAlpha, i)
			self.offset = image.offset
			try:
				image.read_image()
				if combine:
					self.images.paste(image.image, (image.xOffset, image.yOffset))
				else:
					self.images.append(image)
			except ImageError as e:
				continue
			except IndexError as e:
				error("IndexError!")
				print(e)
				continue
