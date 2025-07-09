from PIL import Image
from pathlib import Path
from io import BytesIO


def crop_and_flip(image: Image.Image, base_name: str, ext: str) -> list[tuple[str, BytesIO]]:
    w, h = image.size
    outputs: list[tuple[str, BytesIO]] = []

    def add(img: Image.Image, suffix: str):
        buffer = BytesIO()
        filename = f"{base_name}_{suffix}.{ext}"
        fmt = (image.format or ext).upper()
        if fmt == "JPG":
            fmt = "JPEG"
        img.save(buffer, format=fmt)
        buffer.seek(0)
        outputs.append((filename, buffer))

    # Original
    add(image, "original")

    # Crops
    crops = {
        "top_half": (0, 0, w, h // 2),
        "bottom_half": (0, h // 2, w, h),
        "top_left": (0, 0, w // 2, h // 2),
        "top_right": (w // 2, 0, w, h // 2),
        "bottom_left": (0, h // 2, w // 2, h),
        "bottom_right": (w // 2, h // 2, w, h),
    }

    for name, box in crops.items():
        cropped = image.crop(box)
        add(cropped, name)

    # Flip all existing
    originals = outputs.copy()
    for filename, buffer in originals:
        img = Image.open(buffer)
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        flip_name = filename.replace(f".{ext}", f"_flip.{ext}")
        flip_buffer = BytesIO()
        fmt = (img.format or ext).upper()
        if fmt == "JPG":
            fmt = "JPEG"
        flipped.save(flip_buffer, format=fmt)
        flip_buffer.seek(0)
        outputs.append((flip_name, flip_buffer))

    return outputs
