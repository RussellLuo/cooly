import os
from setuptools import setup, find_packages


basedir = os.path.dirname(__file__)


def get_info(name):
    with open(os.path.join(basedir, 'web_app/__init__.py')) as f:
        locals = {}
        exec(f.read(), locals)
        return locals[name]


def find_data_files(install_dir, src_dir):
    """Install all files recursively from `src_dir` into `install_dir`."""
    data_files = []
    for root, _, files in os.walk(src_dir):
        install_root = os.path.join(install_dir, root)
        install_files = [os.path.join(root, f) for f in files]
        data_files.append((install_root, install_files))
    return data_files


setup(
    name='Web-App',
    version=get_info('__version__'),
    author=get_info('__author__'),
    author_email=get_info('__email__'),
    maintainer=get_info('__author__'),
    maintainer_email=get_info('__email__'),
    description=get_info('__doc__'),
    license=get_info('__license__'),
    long_description=get_info('__doc__'),
    packages=find_packages(),
    install_requires=['Flask==1.0'],
    # Include package data recursively in MANIFEST.in
    include_package_data=True,
    data_files=find_data_files('data', 'etc'),
)
