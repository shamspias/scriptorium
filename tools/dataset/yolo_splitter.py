import shutil
import random
from pathlib import Path
from typing import List, Tuple


class YoloDatasetSplitter:
    IMAGE_EXTS = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff']

    def __init__(self,
                 base_path: str,
                 train_ratio: float = 0.8,
                 val_ratio: float = 0.1,
                 test_ratio: float = 0.1,
                 seed: int = 42):
        self.base = Path(base_path)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

        # Potential source splits
        self.src_splits = ['train', 'valid', 'test']
        self.src_dirs = {
            split: {
                'images': self.base / split / 'images',
                'labels': self.base / split / 'labels'
            } for split in self.src_splits
        }

        # Temporary combined folder
        self.all_images = self.base / 'all' / 'images'
        self.all_labels = self.base / 'all' / 'labels'

        # Where to dump unmatched
        self.issues_images = self.base / 'issue_files' / 'images'
        self.issues_labels = self.base / 'issue_files' / 'labels'

        # Final splits (note 'valid' instead of 'val')
        self.dest_splits = ['train', 'valid', 'test']
        self.dest_dirs = {
            split: {
                'images': self.base / split / 'images',
                'labels': self.base / split / 'labels'
            } for split in self.dest_splits
        }

    def _make_folder(self, path: Path):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    def _gather_and_separate(self) -> List[Tuple[Path, Path]]:
        """
        - Scans all existing split dirs for images & labels.
        - Moves unmatched into issue_files/.
        - Returns only the matched (img, lbl) pairs.
        """
        # collect all image paths and label paths
        img_paths = []
        lbl_paths = []
        for split, dirs in self.src_dirs.items():
            img_dir, lbl_dir = dirs['images'], dirs['labels']
            if img_dir.is_dir():
                for ext in self.IMAGE_EXTS:
                    img_paths += list(img_dir.glob(ext))
            if lbl_dir.is_dir():
                lbl_paths += list(lbl_dir.glob('*.txt'))

        # map stem -> path
        imgs_by_stem = {p.stem: p for p in img_paths}
        lbls_by_stem = {p.stem: p for p in lbl_paths}

        # ensure issue dirs exist
        self.issues_images.parent.mkdir(parents=True, exist_ok=True)
        self.issues_labels.parent.mkdir(parents=True, exist_ok=True)
        self._make_folder(self.issues_images)
        self._make_folder(self.issues_labels)

        pairs = []
        # matched
        for stem, img_p in imgs_by_stem.items():
            if stem in lbls_by_stem:
                pairs.append((img_p, lbls_by_stem[stem]))
            else:
                # no label → move image to issues
                shutil.move(str(img_p), self.issues_images / img_p.name)

        # any label without image
        for stem, lbl_p in lbls_by_stem.items():
            if stem not in imgs_by_stem:
                shutil.move(str(lbl_p), self.issues_labels / lbl_p.name)

        return pairs

    def combine_all(self, pairs: List[Tuple[Path, Path]]):
        """Copy matched pairs into all/images + all/labels."""
        self._make_folder(self.all_images)
        self._make_folder(self.all_labels)
        for img_p, lbl_p in pairs:
            shutil.copy(img_p, self.all_images / img_p.name)
            shutil.copy(lbl_p, self.all_labels / lbl_p.name)

    def remove_old_splits(self):
        """Delete original train/, valid/, test/ directories."""
        for split in self.src_splits:
            folder = self.base / split
            if folder.exists():
                shutil.rmtree(folder)

    def split_and_distribute(self):
        """Shuffle combined set, split, and move into train/ valid/ test/."""
        all_imgs = list(self.all_images.iterdir())
        random.seed(self.seed)
        random.shuffle(all_imgs)

        n = len(all_imgs)
        n_val = int(self.val_ratio * n)
        n_test = int(self.test_ratio * n)
        # rest is train
        splits = {
            'valid': all_imgs[:n_val],
            'test': all_imgs[n_val:n_val + n_test],
            'train': all_imgs[n_val + n_test:]
        }

        # create dest folders
        for split in self.dest_splits:
            self._make_folder(self.dest_dirs[split]['images'])
            self._make_folder(self.dest_dirs[split]['labels'])

        # move files
        for split, imgs in splits.items():
            for img_p in imgs:
                stem = img_p.stem
                lbl_p = self.all_labels / f"{stem}.txt"
                dst_img = self.dest_dirs[split]['images'] / img_p.name
                dst_lbl = self.dest_dirs[split]['labels'] / lbl_p.name

                shutil.move(str(img_p), dst_img)
                if lbl_p.exists():
                    shutil.move(str(lbl_p), dst_lbl)
                else:
                    print(f"⚠️  Missing label for {img_p.name} during split.")

    def clean_all_folder(self):
        """Remove the temporary 'all' folder after splitting."""
        all_folder = self.base / 'all'
        if all_folder.exists():
            shutil.rmtree(all_folder)

    def run(self):
        print("🗂️  Gathering & separating matched pairs (unmatched → issue_files)...")
        pairs = self._gather_and_separate()
        print(f"   → {len(pairs)} matched image/label pairs found.")

        print("🔄  Combining matched pairs into 'all/'...")
        self.combine_all(pairs)

        print("🧹  Removing old train/valid/test folders...")
        self.remove_old_splits()

        print("✂️  Splitting into 80% train / 10% valid / 10% test ...")
        self.split_and_distribute()

        print("🗑️  Cleaning up temporary 'all' directory...")
        self.clean_all_folder()

        print("✅  Done.")
        print(" • Matched data → all/ → split → train/, valid/, test/")
        print(" • Issues (no partner) → issue_files/images & issue_files/labels")


if __name__ == '__main__':
    splitter = YoloDatasetSplitter(base_path='/workspace/PlantDoc-1')
    splitter.run()
