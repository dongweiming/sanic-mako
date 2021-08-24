"""
sanic-mako
----------

"""
import os
import re
import sys
import codecs
from setuptools import setup

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'sanic_mako.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

setup(
    name='Sanic-Mako',
    version=version,
    url='https://github.com/dongweiming/sanic-mako',
    license='Apache 2',
    author='DongWeiming',
    author_email='ciici123@gmail.com',
    description='Mako templating support for Sanic.',
    long_description=__doc__,
    py_modules=['sanic_mako'],
    zip_safe=False,
    platforms='any',
    install_requires=['Werkzeug', 'Mako'],
    long_description_content_type="text/markdown",
    classifiers=[
        'Framework :: AsyncIO',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
