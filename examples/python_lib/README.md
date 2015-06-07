# Python Library Example

An example showing how to deploy a Python library.


## Usage

### 1. Install tools

Tools to install on the local server:

+ Cooly

Tools to install on the build server:

+ Cooly

### 2. Download the example

```
$ cd /tmp
$ git clone https://github.com/RussellLuo/cooly.git
$ cd cooly/examples/python_lib
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
