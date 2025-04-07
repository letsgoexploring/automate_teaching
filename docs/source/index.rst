.. Teaching Tools documentation master file, created by
   sphinx-quickstart on Fri Jan 24 08:37:49 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. Use sphinx==5.1!!!



About ``automate_teaching``
============================

``automate_teaching`` is a Python package with utilities to assist educators, particularly in higher education, with tasks such as managing homework, creating multiple choice exams, sending emails, interacting with Google Calendar, and working with LaTeX files. The utilities for interacting with Gmail and Google Calendar may be useful in contexts outside of education. 

Capabilities include:

* Send and manage Gmail messages.
* Add, find, and delete Google Calendar events.
* Manage and format homework answers for Gradescope.
* Tools for creating multiple choice exams.
* Compile LaTeX files and create handouts for Beamer slides.
* Convert Jupyter Notebooks to Python scripts or HTML files.

Installation
------------

Install ``automate_teaching`` from PyPI with the shell command::


	pip install automate_teaching


Or download the source for version |release| here: |release_url|.


Contents:
---------

.. toctree::
   :maxdepth: 1

   exam
   google
   latex
   homework
   functions

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`search`