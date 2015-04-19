import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "an_example_pypi_project",
    version = "0.0.1-SNAPSHOT",
    author = "Namrata Mendon",
    author_email = "mendon.namrata@gmail.com",
    description = (" A class project"),
    license = "BSD",
    keywords = "example documentation tutorial",
    packages= find_packages(),
    long_description=read('README'),
    entry_points = {
		'console_scripts':[
			'start_server =  bookz.app:start_server',
			'stop_server = bookz.app:stop_server'
		]
	},

	# Helps include the templates
	# Use bower for the js and css component install
	package_data={'bookz': [
        'templates/*.html', 'static/css/*.css', 'static/js/*.js', 'config/*']},

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
