#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path

from kellog import debug, info, warning, error

from dataFile import DataFile

from image import ImgType

# ==================================================================================================
def main(args):
	dataFiles = (args.src / "Data").glob("*.sg3") if args.src.resolve().is_dir() else [args.src]
	for filePath in dataFiles:
		info(f"Reading from {filePath.name}")
		bitmapIDs = set()
		dataFile = DataFile(filePath, args.combine, bitmapIDs)
		for bitmap in dataFile.bitmaps:
			# TODO ignore system
			if args.extract:
				if args.subdirs:
					bitmapDir = (args.extract / filePath.stem / Path(bitmap.filename).stem)
				else:
					bitmapDir = (args.extract / Path(bitmap.filename).stem)
			# TODO Bad form, different type returned depending on arguments
			if not args.dryrun:
				if args.combine:
					bitmap.images.save(f"{bitmapDir}.png")
				else:
					for image in bitmap.images:
						bitmapDir.mkdir(parents=True, exist_ok=True)
						image.save(bitmapDir / f"{image.imgNum}_{image.imgType}.png")


# ==================================================================================================
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("src", metavar="SRC", help="Location of either the Pharaoh/Cleopatra root installation directory, or a specific `.sg3` file")
	parser.add_argument("extract", metavar="OUT_DIR", help="Extract all images to this location")
	parser.add_argument("-s", "--subdirs", action="store_true", help="Use subdirectories with original data file names")
	parser.add_argument("-d", "--dryrun", action="store_true", help="Don't save anything")
	parser.add_argument("-c", "--combine", action="store_true", help="Combine individual images back into their full bitmap")

	args = parser.parse_args()
	args.src = Path(args.src)
	args.extract = Path(args.extract)

	return args


# ==================================================================================================
if __name__ == "__main__":
	main(parse_args())
