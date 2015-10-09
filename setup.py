import os
from setuptools import setup, find_packages


basedir = os.path.dirname(__file__)


def get_info(name):
    with open(os.path.join(basedir, 'cooly/__init__.py')) as f:
        locals = {}
        exec(f.read(), locals)
        return locals[name]


setup(
    name='Cooly',
    version=get_info('__version__'),
    author=get_info('__author__'),
    author_email=get_info('__email__'),
    maintainer=get_info('__author__'),
    maintainer_email=get_info('__email__'),
    keywords='Cooly, Python Deployment',
    description=get_info('__doc__'),
    license=get_info('__license__'),
    long_description=get_info('__doc__'),
    packages=find_packages(),
    url='https://github.com/RussellLuo/cooly',
    install_requires=[
        'Fabric==1.10.1',
        'PyYAML>=3.10',
        'Click==4.0',
        'platter>=1.0-dev',
    ],
    dependency_links=[
        'https://github.com/RussellLuo/platter/archive/master.zip#egg=platter-1.0-dev',
    ],
    entry_points={
        'console_scripts': [
            'cooly = cooly.cli:cli',
        ],
    },
)
