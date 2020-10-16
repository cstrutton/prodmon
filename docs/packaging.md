## Trying to build an installable Debian package


### Install Dependancies

```
apt-get install dh-virtualenv devscripts
```

### prep the requirements.txt file
Then use pip-compile (which is available by installing the PyPI package pip-tools)
```
pip-compile requirements.in > requirements.txt
```

### build the package
```
debuild -b -us -uc
```