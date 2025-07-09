# OneShotDataSetPrep

Simple console tool to generate a one-shot dataset from a single image.

## Usage

```bash
python main.py path/to/image.jpg -o output_dir
```

Creates 14 cropped and flipped images inside `output_dir`.

## Webserver API

After installing the requirements, you can start a small Flask server that
accepts image uploads. Generated datasets are stored in an archive directory and
can be downloaded from the web interface.
Only the ten most recent datasets are kept; older archives are deleted
automatically.

```bash
python run.py
```

Send a `POST` request with form-data field `image` to `http://localhost:7860/upload`.

## Maintainer Script

The repository ships with `maintainer.sh` to ease installation and updates. By default it installs the app under `/opt/OneShot` and manages a Python virtual environment automatically.

```bash
./maintainer.sh install         # clone repo and install dependencies
./maintainer.sh start           # run the web UI
./maintainer.sh update          # pull latest code and update deps
./maintainer.sh uninstall       # remove installation
./maintainer.sh create-admin <user> <password>
```

All commands run using the virtual environment in `/opt/OneShot/venv`.
