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
   cropped and flipped images and stores them as a ZIP file in the user's
   personal directory or the selected team directory. Each user may keep up to
   ten personal datasets while every team can store fifty datasets. The page
   refreshes after processing so the ZIP can be downloaded from the archive
   list.
3. **Deletion** – Users remove old datasets themselves once the quota is
   reached.
4. **Teams** – A user can create a team and invite other members. Uploads may be
   stored in a team archive which is shared by all members. Personal dataset
   sharing has been removed.

## Admin view

Administrators have two ways to manage the system:

* A special **User Administration** page is available once logged in as an admin.
  Here new users can be created or removed and the global registration option can
  be toggled.
* The command `./maintainer.sh create-admin <user> <pass>` can create an initial
  admin account on the command line.

## Team management

The creator of a team becomes its head and can invite members from the
"Manage Team" page. Every team has its own archive directory and may store up to
fifty uploads (configurable via the `ARCHIVE_LIMIT_TEAM` environment variable).

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
