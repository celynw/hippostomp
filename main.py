#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path

from kellog import debug, info, warning, error

# ==================================================================================================
class DataFile():
	headerSize = 680
	# ----------------------------------------------------------------------------------------------
	def __init__(self, filePath):
		self.filePath = filePath
		self.offset = 0

		self.read_header()
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
