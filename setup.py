from distutils.core import setup

# Please run
# python setup.py install

setup(
    name = 'wikipediafs',
    version = '0.1',
    author = 'Mathieu Blondel',
    author_email = 'mblondel@users.sourceforge.net',
    url = 'http://wikipediafs.sourceforge.net',
    packages = ['wikipediafs'],
    package_dir = {'wikipediafs':'src/wikipediafs/'},
    scripts = ['src/mount.wikipediafs'],
)