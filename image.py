#!/usr/bin/env python3
import colored_traceback.auto
from tqdm import tqdm
from PIL import Image as PILImage
import textwrap
from enum import Enum

from kellog import debug, info, warning, error

# ==================================================================================================
class ImgType(Enum):
	unknown = 0
	plain = 1
	isometric = 2
	sprite = 3
	# ----------------------------------------------------------------------------------------------
	def __str__(self):
		return self.name.capitalize()


types = {
	ImgType.plain: [0, 1, 10, 12, 13],
	ImgType.isometric: [30],
	ImgType.sprite: [256, 257, 276],
}
# ==================================================================================================
def get_img_type(imgType):
	for k, v in types.items():
		if imgType in v:
			return k
	# raise ValueError(f"Unknown type: {imgType}")
	error(f"Unknown type: {imgType}")
	return ImgType.unknown


# ==================================================================================================
class Image():
	isometricTileWidth = 58
	isometricTileHeight = 30
	isometricTileBytes = 1800
	isometricLargeTileWidth = 78
	isometricLargeTileHeight = 40
	isometricLargeTileBytes = 3200
	# ----------------------------------------------------------------------------------------------
	def __init__(self, filePath, offset, version):
		self.filePath = filePath
		self.offset = offset

		self.read_header(includeAlpha=version >= 0xd6)
		self.read_image()

	# ----------------------------------------------------------------------------------------------
	def read_header(self, includeAlpha):
		with open(self.filePath, "rb") as f:
			f.seek(self.offset)
			self.offset555 = int.from_bytes(f.read(4), byteorder="little")
			self.length = int.from_bytes(f.read(4), byteorder="little")
			self.uncompressed_length = int.from_bytes(f.read(4), byteorder="little")
			f.seek(4, 1)
			self.invert_offset = int.from_bytes(f.read(4), byteorder="little", signed=True)
			self.width = int.from_bytes(f.read(2), byteorder="little", signed=True)
			self.height = int.from_bytes(f.read(2), byteorder="little", signed=True)
			f.seek(26, 1)
			self.imgType = get_img_type(int.from_bytes(f.read(2), byteorder="little"))
			self.flags = f.read(4)
			self.bitmap_id = int.from_bytes(f.read(1), byteorder="little")
			f.seek(7, 1)

			if includeAlpha:
				self.alpha_offset = int.from_bytes(f.read(4), byteorder="little")
				self.alpha_length = int.from_bytes(f.read(4), byteorder="little")
			else:
				self.alpha_length = 0

			self.offset = f.tell()

	# ----------------------------------------------------------------------------------------------
	def __repr__(self):
		return f"<{__class__.__name__}: {self.imgType} {self.width}x{self.height}>"

	# ----------------------------------------------------------------------------------------------
	def __str__(self):
		return textwrap.dedent(f"""
		Image #{self.bitmap_id} ({self.width}x{self.height})
		""").strip()

	# ----------------------------------------------------------------------------------------------
	@property
	def shape(self):
		return (self.width, self.height)

	# ----------------------------------------------------------------------------------------------
	def show(self):
		self.image.show()

	# ----------------------------------------------------------------------------------------------
	def read_image(self):
		with open(self.filePath, "rb") as f:
			f.seek(self.offset)
			image = [(0, 0, 0, 0)] * self.width * self.height
			with open(self.filePath.with_suffix(".555"), "rb") as f2:
				data_length = self.length + self.alpha_length
				if data_length <= 0:
					error(f"Data length invalid: {data_length}")
					return None
				f2.seek(self.offset555 - self.flags[0])
				buffer = f2.read(data_length)
				# data_read = int.from_bytes(f2.read(1), byteorder="little") # Somehow externals have 1 byte added to their offset
				# if (data_length != data_read):
				# 	if (data_read + 4 == data_length) and (f2.eof()):
				# 		# Exception for some C3 graphics: last image is 'missing' 4 bytes
				# 		warning("Not implemented")
				# 		# buffer[data_read] = buffer[data_read+1] = 0;
				# 		# buffer[data_read+2] = buffer[data_read+3] = 0;
				# debug(data_read)
				# debug(len(buffer))

			self.image = PILImage.new("RGBA", (self.width, self.height))
			if self.imgType == ImgType.plain:
				i = 0
				for y in range(self.width):
					for x in range(self.height):
						pixel = self.set555Pixel(buffer[i] | (buffer[i + 1] << 8), self.width)
						image[(y * self.width) + x] = (pixel & 255, (pixel & 255 << 8) >> 8, (pixel & 255 << 16) >> 16, pixel >> 24)
						i += 2
			elif self.imgType == ImgType.isometric:
				size = self.flags[3]
				height = int((self.width + 2) / 2) # 58 -> 30, 118 -> 60, etc.
				y_offset = self.height - height
				if size == 0:
					# Derive the tile size from the height (more regular than width)
					# Note that this causes a problem with 4x4 regular vs 3x3 large:
					# 4 * 30 = 120; 3 * 40 = 120 -- give precedence to regular
					if height % self.isometricTileHeight == 0:
						size = int(height / self.isometricTileHeight)
					elif height % self.isometricLargeTileHeight == 0:
						size = int(height / self.isometricLargeTileHeight)

				# Determine whether we should use the regular or large (emperor) tiles
				if self.isometricTileHeight * size == height:
					tileBytes = self.isometricTileBytes
					tileHeight = self.isometricTileHeight
					tileWidth = self.isometricTileWidth
				elif self.isometricLargeTileHeight * size == height:
					tileBytes = self.isometricLargeTileBytes
					tileHeight = self.isometricLargeTileHeight
					tileWidth = self.isometricLargeTileWidth
				else:
					error("Unknown tile size")
					return None

				# Check if buffer length is enough: (width + 2) * height / 2 * 2bpp */
				if (self.width + 2) * height != self.uncompressed_length:
					error("Data length doesn't match footprint size")
					return None

				i = 0
				for y in range(size + (size - 1)):
					x_offset = size - y - 1 if y < size else y - size + 1
					x_offset *= tileHeight
					wd = y + 1 if y < size else 2 * size - y - 1
					for wdx in range(wd):
						halfHeight = int(tileHeight / 2)
						x, y, i = 0, 0, 0
						for y in range(halfHeight):
							start = tileHeight - 2 * (y + 1)
							end = tileWidth - start
							for x in range(start, end):
								pixel = self.set555Pixel((buffer[i + 1] << 8) | buffer[i], wd)
								image[(y * self.width) + x] = (pixel & 255, (pixel & 255 << 8) >> 8, (pixel & 255 << 16) >> 16, pixel >> 24)
								i += 2
						for y in range(halfHeight, tileHeight):
							start = 2 * y - tileHeight
							end = tileWidth - start
							for x in range(start, end):
								pixel = self.set555Pixel((buffer[i + 1] << 8) | buffer[i], wd)
								image[(y * self.width) + x] = (pixel & 255, (pixel & 255 << 8) >> 8, (pixel & 255 << 16) >> 16, pixel >> 24)
								i += 2
						x_offset += tileWidth + 2
						i += 1
					y_offset += int(tileHeight / 2)
				i, x, y = 0, 0, 0
				while i < self.length:
					c = buffer[i]
					i += 1
					if c == 255:
						# The next byte is the number of pixels to skip
						x += buffer[i]
						i += 1
						while (x >= self.width):
							y += 1
							x -= self.width
					else:
						# c is the number of image data bytes
						for j in range(c):
							pixel = self.set555Pixel(buffer[i] | (buffer[i + 1] << 8), self.width)
							image[(y * self.width) + x] = (pixel & 255, (pixel & 255 << 8) >> 8, (pixel & 255 << 16) >> 16, pixel >> 24)
							x += 1
							if x >= self.width:
								y += 1
								x = 0
							i += 2
			elif self.imgType == ImgType.sprite:
				i, x, y = 0, 0, 0
				while i < self.length:
					c = buffer[i] # uint8_t
					i += 1
					if c == 255:
						# The next byte is the number of pixels to skip
						x += buffer[i]
						i += 1
						while (x >= self.width):
							y += 1
							x -= self.width
					else:
						# c is the number of image data bytes
						for j in range(c):
							pixel = self.set555Pixel(buffer[i] | (buffer[i + 1] << 8), self.width)
							image[(y * self.width) + x] = (pixel & 255, (pixel & 255 << 8) >> 8, (pixel & 255 << 16) >> 16, pixel >> 24)
							x += 1
							if x >= self.width:
								y += 1
								x = 0
							i += 2
			self.image.putdata(image)

	# ----------------------------------------------------------------------------------------------
	def set555Pixel(self, colour, width):
		rgba = 0xff000000
		if colour == 0xf81f:
			return rgba

		# Red: 11-15 -> 4-8 | 13-15 -> 1-3
		rgba |= ((colour & 0x7c00) >> 7) | ((colour & 0x7000) >> 12)
		# Green: 6-10 -> 12-16 | 8-10 -> 9-11
		rgba |= ((colour & 0x3e0) << 6) | ((colour & 0x380) << 1) # 0x300
		# Blue: 1-5 -> 20-24 | 3-5 -> 17-19
		rgba |= ((colour & 0x1f) << 19) | ((colour & 0x1c) << 14)

		return rgba
