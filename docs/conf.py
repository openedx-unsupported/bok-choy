# -*- coding: utf-8 -*-

import os
import sys
import edx_theme


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon', 'edx_theme']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# Substitutions for all pages
rst_epilog = """
.. _Bok Choy: https://github.com/edx/bok-choy
.. _Selenium: http://www.seleniumhq.org
.. _Python: http://python.org
"""

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'bok-choy'
copyright = edx_theme.COPYRIGHT
author = edx_theme.AUTHOR

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.6.2'
# The full version, including alpha/beta/rc tags.
release = '0.6.2'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'edx_theme'
html_theme_path = [edx_theme.get_html_theme_path()]
html_favicon = os.path.join(html_theme_path[0], 'edx_theme', 'static', 'css', 'favicon.ico')

# Output file base name for HTML help builder.
htmlhelp_basename = 'bok-choydoc'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'bok-choy.tex', u'bok-choy Documentation',
   author, 'manual'),
]


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'bok-choy', u'bok-choy Documentation',
     [author], 1)
]


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'bok-choy', u'bok-choy Documentation',
   author, 'bok-choy', 'One line description of project.',
   'Miscellaneous'),
]


# -- Autodoc options -----------------------------------------------------------
autoclass_content = 'both'
