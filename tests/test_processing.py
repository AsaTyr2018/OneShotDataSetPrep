import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.processing import crop_and_flip
from PIL import Image


def test_crop_and_flip():
    img = Image.new("RGB", (400, 400), color="red")
    result = crop_and_flip(img, 'test', 'jpg')
    assert len(result) == 14
    filenames = [name for name, _ in result]
    assert 'test_top_left_flip.jpg' in filenames
    assert 'test_bottom_right.jpg' in filenames
