# OneShot Dataset Prep

OneShot Dataset Prep creates a small training set from a single image. The
application consists of a Flask based web interface with optional user
management. All binary dependencies are installed via the supplied
`maintainer.sh` script.

## User view

1. **Registration/Login** – Users may sign up (if enabled) or an admin can
   create accounts using the maintainer script. After logging in they are
directed to the upload page.
2. **Uploading** – Drag and drop an image onto the form. The server generates 14
   cropped and flipped images, stores them as a ZIP file and keeps the ten most
   recent archives for each user. The page refreshes after processing so the ZIP
   can be downloaded from the archive list.
3. **Sharing** – The owner of an archive can share it with another registered
   user by entering their username. Shared datasets appear in both users'
   archive list.
4. **Deletion** – Each user can delete the datasets they own at any time.

## Admin view

Administrators have two ways to manage the system:

* A special **User Administration** page is available once logged in as an admin.
  Here new users can be created or removed and the global registration option can
  be toggled.
* The command `./maintainer.sh create-admin <user> <pass>` can create an initial
  admin account on the command line.

## Setup using `maintainer.sh`

The application is meant to be installed through the maintainer script. Run all
commands with suitable privileges if installing system wide.

```bash
# clone into /opt/OneShot and install dependencies
./maintainer.sh install

# optional: create the first admin user
./maintainer.sh create-admin admin secret

# start the web UI manually
./maintainer.sh start
```

During the installation step you will be asked whether the service should be
registered with systemd. Choosing **yes** calls `install_service.sh` which writes
`/etc/systemd/system/oneshot.service` and enables the service immediately.

## Updating and maintenance

To update the code base and dependencies use:

```bash
./maintainer.sh update
```

If the service was running it will automatically restart. To completely remove
the installation use `./maintainer.sh uninstall`.

## Manual run for development

Developers who simply cloned the repository can start the Flask server directly:

```bash
python run.py
```

The web interface will be available on port `7860` by default.  To change the
port, edit ``config.json`` and set the ``"port"`` value before running the
application.
