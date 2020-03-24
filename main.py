#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path
from tqdm import tqdm
from PIL import Image

from kellog import debug, info, warning, error

# ==================================================================================================
class DataFile():
	headerSize = 680
	bitmapRecordSize = 200
	# ----------------------------------------------------------------------------------------------
	def __init__(self, filePath):
		self.filePath = filePath
		self.offset = 0

		self.read_header()
		self.read_bitmaps()
		self.offset = self.headerSize + (self.get_max_bitmap_records() * self.bitmapRecordSize)
		self.read_images(includeAlpha=self.version >= 0xd6)

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

		info(f"# bitmaps: {self.numBitmapRecords}")
		info(f"# images: {self.numImageRecords}")

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
			for bitmap in range(self.numBitmapRecords):
				filename = f.read(65).rstrip(b"\x00").decode("ascii")
				comment = f.read(51).rstrip(b"\x00").decode("ascii")

				width = int.from_bytes(f.read(4), byteorder="little")
				height = int.from_bytes(f.read(4), byteorder="little")
				numImages = int.from_bytes(f.read(4), byteorder="little")
				startIndex = int.from_bytes(f.read(4), byteorder="little")
				endIndex = int.from_bytes(f.read(4), byteorder="little")

				debug(f"BITMAP {bitmap}:")
				debug(f"  filename: {filename}")
				debug(f"  comment: {comment}")
				debug(f"  width: {width}")
				debug(f"  height: {height}")
				debug(f"  numImages: {numImages}")
				debug(f"  startIndex: {startIndex}")
				debug(f"  endIndex: {endIndex}")

				f.seek(64, 1)
				self.offset = f.tell()

	# ----------------------------------------------------------------------------------------------
	def read_images(self, includeAlpha: bool):
		with open(self.filePath, "rb") as f:
			f.seek(self.offset)
			for record in tqdm(range(self.numImageRecords)):
				offset = int.from_bytes(f.read(4), byteorder="little")
				length = int.from_bytes(f.read(4), byteorder="little")
				uncompressed_length = int.from_bytes(f.read(4), byteorder="little")
				f.seek(4, 1)
				invert_offset = int.from_bytes(f.read(4), byteorder="little", signed=True)
				width = int.from_bytes(f.read(2), byteorder="little", signed=True)
				height = int.from_bytes(f.read(2), byteorder="little", signed=True)
				f.seek(26, 1)
				imgType = int.from_bytes(f.read(2), byteorder="little")
				flags = f.read(4)
				debug(flags)
				debug(flags[3])
				bitmap_id = int.from_bytes(f.read(1), byteorder="little")
				f.seek(7, 1)

				if includeAlpha:
					alpha_offset = int.from_bytes(f.read(4), byteorder="little")
					alpha_length = int.from_bytes(f.read(4), byteorder="little")
				else:
					alpha_length = 0

				self.offset = f.tell()

				if record == 0:
					continue # First one is always a dummy record

				debug(f"IMAGE {record}:")
				debug(f"  offset: {offset}")
				debug(f"  length: {length}")
				debug(f"  uncompressed_length: {uncompressed_length}")
				debug(f"  invert_offset: {invert_offset}")
				debug(f"  width: {width}")
				debug(f"  height: {height}")
				debug(f"  imgType: {imgType}")
				debug(f"  flags: {flags}")
				debug(f"  bitmap_id: {bitmap_id}")

				image = b""
				with open(self.filePath.with_suffix(".555"), "rb") as f2:
					data_length = length + alpha_length
					if data_length <= 0:
						error(f"Data length invalid: {data_length}")
						continue
					f2.seek(offset - flags[0])
					buffer = b""
					for byte in range(data_length):
						buffer += f2.read(1)
					# data_read = int.from_bytes(f2.read(1), byteorder="little") # Somehow externals have 1 byte added to their offset
					# if (data_length != data_read):
					# 	if (data_read + 4 == data_length) and (f2.eof()):
					# 		# Exception for some C3 graphics: last image is 'missing' 4 bytes
					# 		warning("Not implemented")
					# 		# buffer[data_read] = buffer[data_read+1] = 0;
					# 		# buffer[data_read+2] = buffer[data_read+3] = 0;
					# debug(data_read)
					# debug(len(buffer))

				if imgType in [0, 1, 10, 12, 13]:
					print("Plain")
					i = 0
					for y in range(width):
						for x in range(height):
							pixel = self.set555Pixel(buffer[i] | (buffer[i + 1] << 8), width)
							image += pixel.to_bytes(4, "little")
							i += 2
					image = Image.frombuffer("RGBA", (width, height), image, "raw")
					# image.show()
				elif imgType == 30:
					print("Isometric")
					warning(f"Not implemented: {imgType}")
					continue
				elif imgType in [256, 257, 276]:
					print("Sprite")
					warning(f"Not implemented: {imgType}")
					continue
				else:
					raise ValueError(f"Unknown type: {imgType}")

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


# ==================================================================================================
def main(args):
	filePath = args.root_dir / "Data" / "AbuSimbel.sg3"
	info(f"Opening {filePath}...")

	dataFile = DataFile(filePath)


# ==================================================================================================
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("root_dir", metavar="DIRECTORY", help="Location of Pharaoh installation directory")

	args = parser.parse_args()
	args.root_dir = Path(args.root_dir)

	return args


# ==================================================================================================
if __name__ == "__main__":
	main(parse_args())
