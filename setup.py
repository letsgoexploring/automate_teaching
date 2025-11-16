from setuptools import setup

import os

# Set version number
release = '0.0.9'

# Save version to version.txt
with open('version.txt','w') as newfile:
    newfile.write(release)

setup(
  name = 'automate_teaching',
  packages = ['automate_teaching'],
  version = release,
  description = 'Functions to assist in course management, particularly economics.',
  author = 'Brian C. Jenkins',
  author_email = 'bcjenkin@uci.edu',
  url = 'https://github.com/letsgoexploring/automate_teaching',
  download_url = 'https://github.com/letsgoexploring/automate_teaching/blob/gh-pages/dist/automate_teaching-'+release+'.tar.gz',
  keywords = ['python','google','gmail','calendar','latex','beamer','exam','multiple choice','gradescope','higher education','teaching'],
  classifiers = [],
  package_data={},
  include_package_data=True,
  license_file="LICENSE",
)