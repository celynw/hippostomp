#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path
from tqdm import tqdm

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
