"""
A clean, class-based utility to convert an HTML file into a plain-text (.txt) file.
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


class HtmlToTextConverter:
    """
    Reads an HTML file, extracts visible text, and writes it to a .txt file.
    """

    def __init__(self, input_path: Path, output_path: Optional[Path] = None) -> None:
        self.input_path = input_path
        self.output_path = output_path or input_path.with_suffix('.txt')
        logging.debug(f"Initialized with input={self.input_path} output={self.output_path}")

    def read_html(self) -> str:
        """Read the HTML content from the input file."""
        try:
            content = self.input_path.read_text(encoding='utf-8')
            logging.debug("Read HTML content successfully.")
            return content
        except FileNotFoundError as e:
            logging.error(f"File not found: {self.input_path}")
            raise
        except Exception as e:
            logging.error(f"Error reading {self.input_path}: {e}")
            raise

    def extract_text(self, html: str) -> str:
        """Extract visible text from HTML, collapse extra whitespace."""
        soup = BeautifulSoup(html, 'html.parser')
        raw_text = soup.get_text(separator='\n')
        lines = (line.strip() for line in raw_text.splitlines())
        filtered = [line for line in lines if line]
        result = '\n'.join(filtered)
        logging.debug("Extracted and cleaned text.")
        return result

    def write_text(self, text: str) -> None:
        """Write the extracted text to the output file."""
        try:
            self.output_path.write_text(text, encoding='utf-8')
            logging.info(f"Saved text to {self.output_path}")
        except Exception as e:
            logging.error(f"Error writing to {self.output_path}: {e}")
            raise

    def convert(self) -> None:
        """High-level method: read HTML, extract text, write to file."""
        html = self.read_html()
        text = self.extract_text(html)
        self.write_text(text)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert an HTML file to a plain-text .txt file."
    )
    parser.add_argument(
        "input", type=Path,
        help="Path to the source HTML file."
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Optional path for the output .txt file."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose (debug) logging."
    )
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    """Configure the logging format and level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    converter = HtmlToTextConverter(
        input_path=args.input,
        output_path=args.output
    )
    converter.convert()


if __name__ == "__main__":
    main()
