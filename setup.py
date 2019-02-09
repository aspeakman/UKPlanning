# python setup.py sdist --formats=gztar,zip
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup
try: # for pip >= 10
    from pip._internal import req, download
except ImportError: # for pip <= 9.0.3
    from pip import req, download
import os
import re

package = 'ukplanning'
name = 'UKPlanning'
details = 'Scrapers for UK planning authorities'

required = [i.strip() for i in open("requirements.txt").readlines()]

# parse_requirements() returns generator of InstallRequirement objects
install_reqs = req.parse_requirements("requirements.txt", session=download.PipSession())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

try:
   import pypandoc
   description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
   description = open('README.md').read()

# get version directly from the file - cannot import package in setup
ff = open(os.path.join(os.path.dirname(__file__), package + '/version.py'))
version_file = ff.read()
ff.close()
version_match = re.search(r"^\s*__version__\s*=\s*['\"]([^'\"]*)['\"]",
                              version_file, re.M)
if not version_match:
    raise RuntimeError("Unable to find version string.")
ver_str = version_match.group(1)

setup(
    name=name,
    version=ver_str,
    author='Andrew Speakman',
    author_email='andrew@speakman.org.uk',
    packages=[package],
    include_package_data=True,
    #scripts=['dddd'],
    #url='http://pypi.python.org/pypi/TowelStuff/',
    license='LICENSE.txt',
    description=details,
    long_description=description,
    install_requires=reqs,
)
