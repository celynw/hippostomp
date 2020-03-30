#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path

from kellog import debug, info, warning, error

from dataFile import DataFile

# ==================================================================================================
def main(args):
	dataFiles = (args.src / "Data").glob("*.sg3") if args.src.resolve().is_dir() else [args.src]
	for filePath in dataFiles:
		info(f"Reading from {filePath.name}")
		dataDir = (args.extract / filePath.stem)
		dataFile = DataFile(filePath)
		for bitmap in dataFile.bitmaps:
			# TODO ignore system
			if args.extract:
				bitmapDir = (dataDir / Path(bitmap.filename).stem)
			for i, image in enumerate(bitmap.images):
				try:
					bitmapDir.mkdir(parents=True, exist_ok=True)
					if not args.dryrun:
						image.save(bitmapDir / f"{i}.png")
				except AttributeError:
					pass


# ==================================================================================================
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("src", metavar="SRC", help="Location of either the Pharaoh/Cleopatra root installation directory, or a specific `.sg3` file")
	parser.add_argument("extract", metavar="OUT_DIR", help="Extract all images to this location")
	parser.add_argument("-d", "--dryrun", action="store_true", help="Don't save anything")

	args = parser.parse_args()
	args.src = Path(args.src)
	args.extract = Path(args.extract)

	return args


# ==================================================================================================
if __name__ == "__main__":
	main(parse_args())
