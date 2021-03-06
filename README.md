# flfm
>Flask File Manager. View files &amp; upload files with style.

Flask File Manager (flfm) is a WSGI application written in Python.

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/m-flak/flfm.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/m-flak/flfm/context:python)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/m-flak/flfm.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/m-flak/flfm/context:javascript)

![flfm_new_gif](https://user-images.githubusercontent.com/35634280/69560476-6ea13080-0f71-11ea-8ffe-999281dac39c.gif)

**Features:**
* **Private sharing between Accounts** _Registered users can share the contents of their folders with other users & vice versa!_
* **Account Management.** _Do you want to serve things publicly or do you want users (or you) to be able to upload & save files privately?_ The choice is yours!
* **Built-in viewer for files.** _Currently Supported: Text Files, Image Files, Video Files_
* _**Configurable**_. Define where users can snoop around and upload (or not) files.
* **SLIDESHOWS!** For image files, you can watch a slideshow of all images in a folder or manually sift through them.
* **Uploading of files.**
* **STREAM VIDEO CONTENT** The built-in viewer can play videos with a properly configured nginx.

**Table of Contents**
* [Configuring flfm](#configuring-flfm)<br/>1. [.env file](#dotenv-file)<br/>2. [rules file](#rules-file)
* [Before Using flfm](#before-using-flfm)
* [MySQL Configuration](#mysql-configuration)
* [Deploying flfm](#deploying-flfm)
* [Running Tests](#running-tests)
* [Creating Initial Accounts](#creating-initial-accounts)
* [Special Thanks](#special-thanks)

### Configuring flfm
flfm is configured via a couple of files. The _.env_ file and the _rules_ file. We'll go over both of these here.
##### dotenv file
First, refer to the _.env\_example_ file. You'll see the following:
```
# Example .env file
# Refer to config.py

# Allow Account Registration
ACCOUNT_REGISTRATION_ENABLED=True

# Where to create users' home folders at
USERS_HOME_FOLDERS=/var/flfm/homes

# Rules file location
RULES_FILE=/etc/flfm.d/rules

# Where to store session files
SESSION_FILE_DIR=/var/cache/flfm/

# Where to sideload videos for streaming thru the viewer
VIEWER_VIDEO_DIRECTORY=/var/cache/videos

# Uncomment to change Application Root
##APPLICATION_ROOT=/flfm

# Customize the banner
##BANNER="My Cool Custom Banner"
# Or use one from a file (limit one line)
##BANNER_TYPE="file"
##BANNER=/etc/flfm.d/banner

# DATABASE
DB_SCHEMA="mysql"
DB_USERNAME="flfm_user"
DB_PASSWORD="PASSWORD"
DB_HOST="localhost"
DB_DATABASE="flfm"
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
AllowUploads=/var/www/public/incoming
```

By default, all paths are non-traversable. If you want a path on your server to be accessible, you'll need to add an **Allowed** rule.

You can explicitly restrict subdirectories within an allowed directory by specifying a **Disallowed** rule with the fully-qualified path to that subdirectory.

###### Nesting:
When it comes to the nesting of rules, **do not** nest an _Allowed_ rule in a _Disallowed_ rule's directory tree. There's no reason to do this, for Flask File Manager will not allow access to files or directories by default in the absence of rules.

*Please note that all of these rules apply only to directories &amp; files that are accessible by the WSGI server's _uid/gid_.*

**Explanation:**<br/>
```Allowed=/path/to/foo``` - _give flfm access to this dir_<br/>
```Disallowed,DisAllowed=/path/to/foo``` - _restrict flfm's access to this dir_<br/>
```AllowUpload,AllowUploads=/path/to/foo``` - _allow a user to upload files in the given directory_<br/>

### Before Using flfm
Configuring the rules and creating a dot-env file is not quite enough to get started with flfm.
Before using flfm, you'll need to _**generate the secret key**_.
This is easily accomplished with running ```make``` in the project root directory _(requires bash & openssl)_.

You'll also want to [setup the database](#mysql-configuration), [create initial accounts](#creating-initial-accounts) _(optional)_, and [deploy](#deploying-flfm).

### MySQL Configuration
MySQL is used to store user credentials. Before you can run migrations, perform the initial setup on your MySQL server. To illustrate:

```SQL
CREATE DATABASE flfm;
CREATE USER 'flfm_user'@'localhost' IDENTIFIED WITH mysql_native_password BY '<PASSWORD_HERE>';
GRANT ALL ON flfm.* TO 'flfm_user'@'localhost';
```
If you're going to run tests, then also:
```SQL
CREATE DATABASE flfm_tests;
GRANT ALL ON flfm_tests.* TO 'flfm_user'@'localhost';
```

Once this is done, you can run migrations to create the table schemas and what-all for _flfm_.

###### Other SQL Backends:

Hate MySQL? Think it's overkill?? While there's no guarantee of compatibility, you can easily change the SQL backend. Look at the _DATABASE_ section of the [.env file](#dotenv-file).

### Deploying flfm
###### systemd Service
Refer to the example systemd service file in _systemd/flfm.service_.

You'll be able to start flfm as a service with ```systemctl```.

For a tutorial concerning this, [check out this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04).

###### nginx Configuration

Checkout the example nginx config file in _nginx/example\_nginx.conf_.

There are two ways to configure nginx as a reverse-proxy for flfm.
* From the root, _or **/**_
* From a location, _such as **/flfm**_

Let's look at how our location directives would look for the first method.

```
        location / {
                proxy_pass http://127.0.0.1:<port>/;
                proxy_redirect off;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }
```
 Now, let's look at how our location directives would look for the second method. **Whatever location you pick must be both in the proxy_pass directive and also set as the APPLICATION_ROOT variable in the [.env file](#dotenv-file).**

```
         location ^~ /flfm {
                proxy_pass http://127.0.0.1:<port>/flfm;
                proxy_redirect off;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }
```

**REMEMBER:**  _APPLICATION_ROOT == Location == End of proxy\_pass_.

##### Playing videos

Make an alias to the **VIEWER_VIDEO_DIRECTORY** variable.

```
        location /videos/ {
            alias <VIEWER_VIDEO_DIRECTORY>;
            mp4;
            mp4_buffer_size 2M;
            mp4_max_buffer_size 10M;
        }
```

Then, set up socket.io in nginx, [Click Here To See How](https://flask-socketio.readthedocs.io/en/latest/#using-nginx-as-a-websocket-reverse-proxy).

### Running Tests
If you wish to run the tests for yourself, ensure that you have created a [.env file](#dotenv-file) pointing to a sample [rules file](#rules-file).

You'll also want to ensure that you have the appropriate directory tree structure to run the tests against as well.

Then, from the project root directory, simply execute:
```
python tests.py
```

### Creating Initial Accounts
FLFM supports account sessions. **_By default_**, account registration is disabled, but you can modify that in your [.env file](#dotenv-file).

To create accounts, use the management script like so:
```
python manage.py createuser
```
Follow the interactive prompts to create the needed account(s) for use with FLFM.

### Special Thanks
Special thanks go out to the following javascript libraries not listed in the project's dependencies:
* [Filepond](https://pqina.nl/filepond/) (for the uploader)
* [js.cookies](https://github.com/js-cookie/js-cookie)
* [base64.js](https://github.com/dankogai/js-base64)
* @FreshVine's [jQuery-cache-images](https://github.com/FreshVine/jQuery-cache-images)
* [video.js](https://videojs.com/)
