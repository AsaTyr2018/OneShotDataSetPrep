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
   cropped and flipped images and stores them as a ZIP file in either the user's
   archive directory (`archives/user_<id>`) or the selected team directory
   (`archives/team_<id>`). Each user may keep up to ten personal datasets while
   every team can store fifty by default. The page refreshes after processing so the ZIP can be
   downloaded from the archive list.
3. **Previewing** – Every upload also stores the generated images under
   `archives/<user|team>_<id>/<archive_name>` without the `.zip` suffix.
   Opening `/preview/<dataset_id>` displays these images in a small gallery.
4. **Deletion** – Users remove old datasets themselves once the quota is
   reached.
5. **Teams** – Team creation is restricted to administrators or users with the
   `can_create_team` permission. Uploads may be stored in a shared team archive
   that all members can access.

## Admin view

Administrators have two ways to manage the system:

* A special **User Administration** page is available once logged in as an admin.
  Here new users can be created or removed and the global registration option can
  be toggled.
* The command `./maintainer.sh create-admin <user> <pass>` can create an initial
  admin account on the command line.
* Adjust dataset quotas by editing `config.json` and setting
  `"archive_limit_user"` and `"archive_limit_team"`.

## Team management

The creator of a team becomes its head and can invite members from the
"Manage Team" page. Only admins or users granted the `can_create_team`
permission can start new teams. Archives are stored under
`archives/team_<id>` and may hold up to fifty uploads by default. Personal
uploads are saved in `archives/user_<id>` and share the same ten-file limit as
the personal archive.

## Setup using `maintainer.sh`

The application is meant to be installed through the maintainer script. Run all
commands with suitable privileges if installing system wide. When running
inside the provided Docker container the script automatically detects the
environment so `create-admin` and `start` work without calling `install` first.

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

## Docker deployment

A prebuilt image is available for running the application in a container. After cloning this repository simply start the service with Docker Compose:

```bash
docker-compose up -d
```

Once the container is running create an initial admin account with:

```bash
docker exec oneshotdatasetprep ./maintainer.sh create-admin <user> <password>
```

The web interface will then be reachable on port `7860`.
