import os
from setuptools import setup, find_packages


basedir = os.path.dirname(__file__)


def get_info(name):
    with open(os.path.join(basedir, 'python_lib/__init__.py')) as f:
        locals = {}
        exec(f.read(), locals)
        return locals[name]


setup(
    name='Python-Lib',
    version=get_info('__version__'),
    author=get_info('__author__'),
    author_email=get_info('__email__'),
    maintainer=get_info('__author__'),
    maintainer_email=get_info('__email__'),
    description=get_info('__doc__'),
    license=get_info('__license__'),
    long_description=get_info('__doc__'),
    packages=find_packages(),
    install_requires=[],
)
