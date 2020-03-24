#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path

from kellog import debug, info, warning, error

from dataFile import DataFile

# ==================================================================================================
def main(args):
	if args.extract:
		args.extract.mkdir(exist_ok=True)
	for filePath in (args.root_dir / "Data").glob("*.sg3"):
		info(f"Reading from {filePath.name}")

		if args.extract:
			dataDir = (args.extract / filePath.stem)
			dataDir.mkdir(exist_ok=True)
		try:
			dataFile = DataFile(filePath)
			for bitmap in dataFile.bitmaps:
				# TODO ignore system
				if args.extract:
					bitmapDir = (dataDir / Path(bitmap.filename).stem)
					bitmapDir.mkdir(exist_ok=True)
				for i, image in enumerate(bitmap.images):
					try:
						image.save(bitmapDir / f"{i}.png")
					except AttributeError:
						pass
		except Exception as e:
			error(e)


# ==================================================================================================
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("root_dir", metavar="DIRECTORY", help="Location of Pharaoh installation directory")
	parser.add_argument("extract", metavar="DIRECTORY", help="Extract all images to this location")

	args = parser.parse_args()
	args.root_dir = Path(args.root_dir)
	args.extract = Path(args.extract)

	return args


# ==================================================================================================
if __name__ == "__main__":
	main(parse_args())
