import argparse
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Tuple


class FullTextSearchRemover:
    """
    Class to search for a query sentence across text files in a directory,
    find the best matching sentence, remove occurrences until no matches remain,
    or remove all regex pattern matches across the files.
    """

    def __init__(self, directory: Path, use_regex: bool = False, threshold: float = 0.6):
        """
        Initialize with the target directory, regex flag, and similarity threshold.
        """
        self.directory = directory
        self.text_files = list(self.directory.glob("*.txt"))
        self.use_regex = use_regex
        self.threshold = threshold
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Split text into sentences using punctuation delimiters.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def similarity(a: str, b: str) -> float:
        """
        Compute a similarity ratio between two strings.
        """
        return SequenceMatcher(None, a, b).ratio()

    def search(self, query: str, top_n: int = 25) -> List[Tuple[Path, str, float]]:
        """
        Search all text files for sentences matching the query via similarity.
        Returns top_n matches as tuples of (file_path, sentence, score).
        """
        matches: List[Tuple[Path, str, float]] = []
        for file in self.text_files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            sentences = self.extract_sentences(text)
            for sentence in sentences:
                score = self.similarity(query, sentence)
                if score >= self.threshold:
                    matches.append((file, sentence, score))
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:top_n]

    def get_best_match(self, query: str) -> Tuple[Path, str, float] | None:
        """
        Retrieve the single best-matching sentence for the query.
        Returns None if no matches above threshold.
        """
        top = self.search(query, top_n=1)
        return top[0] if top else None

    def remove_sentence_from_all(self, sentence: str) -> bool:
        """
        Remove all exact occurrences of the given sentence from every text file.
        Returns True if any file was modified.
        """
        escaped = re.escape(sentence)
        changed = False
        for file in self.text_files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            new_text = re.sub(escaped, "", text)
            if new_text != text:
                file.write_text(new_text, encoding="utf-8")
                logging.info(f"Removed sentence from {file}")
                changed = True
        return changed

    def remove_pattern_from_all(self, pattern: str) -> None:
        """
        Treat the query as a regex and remove all matches across text files.
        """
        regex = re.compile(pattern)
        for file in self.text_files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            new_text = regex.sub('', text)
            if new_text != text:
                file.write_text(new_text, encoding="utf-8")
                logging.info(f"Removed regex matches from {file}")

    def run(self, query: str) -> None:
        """
        Execute removal: either regex-based or similarity-based until no matches.
        """
        if self.use_regex:
            logging.info("Starting regex removal mode.")
            self.remove_pattern_from_all(query)
        else:
            logging.info("Starting similarity removal mode.")
            while True:
                match = self.get_best_match(query)
                if not match:
                    logging.info("No more matches above threshold.")
                    break
                file, sentence, score = match
                logging.info(f"Best match (score={score:.2f}) in {file}: '{sentence}'")
                if not self.remove_sentence_from_all(sentence):
                    logging.info("No removal occurred. Exiting loop.")
                    break
        logging.info("Removal complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Search for a sentence (or regex) and remove matches from text files in a directory."
    )
    # Optional flags
    parser.add_argument(
        "-r", "--regex", action="store_true",
        help="Treat query as regex pattern"
    )
    parser.add_argument(
        "-t", "--threshold", type=float, default=0.6,
        help="Similarity threshold (0-1) for matching sentences"
    )
    # Positional arguments
    parser.add_argument(
        "query", help="Sentence or regex pattern to search for"
    )
    parser.add_argument(
        "directory", type=Path, help="Directory containing .txt files"
    )
    args = parser.parse_args()

    remover = FullTextSearchRemover(
        args.directory, use_regex=args.regex, threshold=args.threshold
    )
    remover.run(args.query)


if __name__ == "__main__":
    main()

