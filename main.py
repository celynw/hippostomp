#!/usr/bin/env python3
import colored_traceback.auto
import argparse
from pathlib import Path

from kellog import debug, info, warning, error

from dataFile import DataFile

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
