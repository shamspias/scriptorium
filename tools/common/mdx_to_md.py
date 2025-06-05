"""
A class-based converter that scans a hardcoded directory for `.mdx` files
and creates corresponding `.md` files with the same content.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class MdxToMdConverter:
    """
    Scans a directory for `.mdx` files and converts each one into a `.md`
    file (by copying its contents). If a `.md` version already exists, it
    will be skipped to avoid overwriting.
    """

    def __init__(self, directory: Path) -> None:
        """
        :param directory: Path to the directory containing `.mdx` files.
        """
        self.directory: Path = directory

    def convert_all(self) -> None:
        """
        Locate every `.mdx` file in `self.directory` (non-recursive) and
        copy it to a new file with a `.md` extension, unless that file
        already exists.
        """
        if not self.directory.exists() or not self.directory.is_dir():
            logging.error("Provided path '%s' is not a valid directory.", self.directory)
            return

        logging.info("Scanning directory: %s", self.directory)

        for item in self.directory.iterdir():
            # Process only regular files ending in .mdx
            if not item.is_file():
                continue

            if item.suffix.lower() != ".mdx":
                continue

            target_path = item.with_suffix(".md")

            if target_path.exists():
                logging.info(
                    "Skipping '%s': '%s' already exists.", item.name, target_path.name
                )
                continue

            try:
                shutil.copyfile(item, target_path)
                logging.info("Converted: '%s' → '%s'", item.name, target_path.name)
            except Exception as e:
                logging.error(
                    "Failed to convert '%s' to '%s': %s",
                    item.name, target_path.name, e
                )


def main() -> None:
    """
    Entry point: define the directory to convert and run the conversion.
    """
    # === EDIT THIS PATH TO YOUR DIRECTORY ===
    TARGET_DIRECTORY = Path("/path/to/your/mdx_files")
    # =======================================

    converter = MdxToMdConverter(directory=TARGET_DIRECTORY)
    converter.convert_all()


if __name__ == "__main__":
    main()
