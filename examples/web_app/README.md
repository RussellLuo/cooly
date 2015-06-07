# Web Application Example

An example showing how to deploy a web application.


## Usage

### 1. Install tools

Tools to install on the local server:

+ Cooly

Tools to install on the build server:

+ Cooly
+ [ConfPlate](https://github.com/verbosemode/confplate)

A pre-build script using `ConfPlate` to generate real `supervisord.conf`, which is specified as `/remote/path/to/prebuild/script/using/confplate.sh` in `cooly.yml`, should also be prepared on the build server:

```bash
#!/bin/bash
set -eu

supervisord_conf="$SOURCE_DIR"/etc/supervisord.conf
supervisord_temp="$SOURCE_DIR"/etc/supervisord.temp
confplate_path=/remote/path/to/confplate/on/build/server

SUPERVISORD_PATH=/supervisord/path/on/deploy/server
LOGGING_PATH=/logging/path/on/deploy/server
APP_PATH=/remote/path/to/install/web_app

${confplate_path}/venv/bin/python ${confplate_path}/confplate/confplate.py ${supervisord_conf} SUPERVISORD_PATH=${SUPERVISORD_PATH} LOGGING_PATH=${LOGGING_PATH} APP_PATH=${APP_PATH} > ${supervisord_temp}

mv ${supervisord_temp} ${supervisord_conf}
```

Tools to install on the deploy server:

+ [Supervisord](http://supervisord.org)

For the first deployment, you should start supervisord by hand on the deploy server like this:

```
$ supervisord -c /remote/path/to/install/web_app/current/data/etc/supervisord.conf
```

### 2. Download the example

```
$ cd /tmp
$ git clone https://github.com/RussellLuo/cooly.git
$ cd cooly/examples/web_app
```

### 3. Initialize git repository

```
$ git init
$ git add .
$ git commit -m 'Initial commit'
```

### 4. Adjust configurations

```
$ vi cooly.yml
```

### 5. Deploy it

```
$ cooly deploy -c cooly.yml
```
