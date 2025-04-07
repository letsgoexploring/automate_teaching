# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sphinx_bootstrap_theme
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# Path to the version file
version_file =  '../../version.txt'

# Read version number
with open(version_file, 'r') as f:
    release = f.read().strip()  # 'release' is the full version number
    version = '.'.join(release.split('.')[:2])  # 'version' is the major.minor version

# Add substitutions to rst_prolog
rst_prolog = f"""
.. |release| replace:: {release}
.. |release_url| replace:: https://github.com/letsgoexploring/automate_teaching/blob/gh-pages/dist/automate_teaching-{release}.tar.gz
"""



# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'automate_teaching'
copyright = '2025, Brian C. Jenkins'
author = 'Brian C. Jenkins'

# The short X.Y version.
version = version
# The full version, including alpha/beta/rc tags.
release = release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc','sphinx.ext.viewcode','nbsphinx','IPython.sphinxext.ipython_console_highlighting','sphinx.ext.mathjax']

templates_path = ['_templates']
exclude_patterns = ['**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
# keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


math_number_all = True



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = 'bootstrap'
# html_static_path = ['_static']
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

html_theme_options = {
    # Disable showing the sidebar. Defaults to 'false'
    # 'nosidebar': True,
    # 'collapse_navigation':True
}



# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'https://docs.python.org/': None}