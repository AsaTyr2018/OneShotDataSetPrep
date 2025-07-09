# OneShotDataSetPrep

Simple console tool to generate a one-shot dataset from a single image.

## Usage

```bash
python main.py path/to/image.jpg -o output_dir
```

Creates 14 cropped and flipped images inside `output_dir`.

## Webserver API

After installing the requirements, you can start a small Flask server that
accepts image uploads and returns a ZIP archive with the processed files.

```bash
python run.py
```

Send a `POST` request with form-data field `image` to `http://localhost:7860/upload`.
