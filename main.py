import argparse
from pathlib import Path
from PIL import Image
from app.processing import crop_and_flip


def main():
    parser = argparse.ArgumentParser(description="Generate dataset from image")
    parser.add_argument('image_path', type=Path, help='Input image path')
    parser.add_argument('-o', '--output', type=Path, default=Path('output'), help='Output directory')
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    img = Image.open(args.image_path)
    base_name = args.image_path.stem
    ext = args.image_path.suffix.lstrip('.')

    results = crop_and_flip(img, base_name, ext)

    for filename, buffer in results:
        out_path = args.output / filename
        with open(out_path, 'wb') as f:
            f.write(buffer.read())

    print(f"Saved {len(results)} images to {args.output}")


if __name__ == '__main__':
    main()
