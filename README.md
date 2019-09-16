# flfm
>Flask File Manager. View files &amp; upload files with style.

Flask File Manager (flfm) is a WSGI application written in Python.

**Features:**
* Built-in viewer for files. _Currently Supported: Text Files, Image files_
* _**Configurable**_. Define where users can snoop around and upload (or not) files.
* **SLIDESHOWS!** For image files, you can watch a slideshow of all images in a folder or manually sift through them.
* Uploading of files.

**Table of Contents**
* [Configuring flfm](#configuring-flfm)<br/>1. [.env file](#dotenv-file)<br/>2. [rules file](#rules-file)
* [Before Using flfm](#before-using-flfm)
* [Deploying flfm](#deploying-flfm)
* [Special Thanks](#special-thanks)

### Configuring flfm
flfm is configured via a couple of files. The _.env_ file and the _rules_ file. We'll go over both of these here.
##### dotenv file
First, refer to the _.env\_example_ file. You'll see the following:
```
# Example .env file
# Refer to config.py

# Rules file location
RULES_FILE=/etc/flfm.d/rules

# Where to store session files
SESSION_FILE_DIR=/var/cache/flfm/

# Uncomment to change Application Root
##APPLICATION_ROOT=/flfm

# Customize the banner
##BANNER="My Cool Custom Banner"
# Or use one from a file (limit one line)
##BANNER_TYPE="file"
##BANNER=/etc/flfm.d/banner
```
**Explanation:**<br/>
```RULES_FILE``` - _the location of the rules file_
It should be in a secure location such as /etc and also be read-only.
```SESSION_FILE_DIR``` - _storage for flask-session files_
[See here for more information](https://github.com/fengsp/flask-session/blob/master/docs/index.rst)

##### rules file
The rules file is plain text and does not support comments. Here is an example:
```
Allowed=/var/www/public
Disallowed=/var/www/public/private
Allowed=/var/www/public/private/not-private
AllowUploads=/var/www/public/incoming
```
By default, in the presence of a rules file, only directories &amp; subdirectories of an _allow rule_ can be traversed. Likewise, the directories &amp; subdirectories of a _disallow rule_ are restricted. If you wish to allow flfm access into a specific folder within a restricted subtree, you can explicitly supply an _allow rule_, which will allow a user to browse that directory **and only that directory**.
Please note that all of these rules apply only to directories &amp; files that are accessible by the WSGI server's _uid/gid_.

**Explanation:**<br/>
```Allowed=/path/to/foo``` - _give flfm access to this dir_<br/>
```Disallowed,DisAllowed=/path/to/foo``` - _restrict flfm's access to this dir_<br/>
```AllowUpload,AllowUploads=/path/to/foo``` - _allow a user to upload files in the given directory_<br/>

### Before Using flfm
Configuring the rules and creating a dot-env file is not quite enough to get started with flfm.
Before using flfm, you'll need to _**generate the secret key**_.
This is easily accomplished with running ```make``` in the project root directory _(requires bash & openssl)_.

### Deploying flfm
Refer to the example systemd service file in _systemd/flfm.service_.

You'll be able to start flfm as a service with ```systemctl```.

For a tutorial concerning this, [check out this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04).

### Special Thanks
Special thanks go out to the following javascript libraries not listed in the project's dependencies:
* [Filepond](https://pqina.nl/filepond/) (for the uploader)
* [js.cookies](https://github.com/js-cookie/js-cookie)
* [base64.js](https://github.com/dankogai/js-base64)
* @FreshVine's [jQuery-cache-images](https://github.com/FreshVine/jQuery-cache-images)
