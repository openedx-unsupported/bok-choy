import os
import sys
from datetime import datetime


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# Substitutions for all pages
rst_epilog = """
.. _Bok Choy: https://github.com/openedx/bok-choy
.. _Selenium: http://www.seleniumhq.org
.. _Python: http://python.org
"""

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'bok-choy'
copyright = f'{datetime.now().year}, The Axim Collaborative' # pylint: disable=redefined-builtin
author = 'The Axim Collaborative'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0.1'
# The full version, including alpha/beta/rc tags.
release = '1.0.1'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_book_theme'
# html_theme_path = []
html_logo = "https://logos.openedx.org/open-edx-logo-color.png"
html_favicon = "https://logos.openedx.org/open-edx-favicon.ico"

# Output file base name for HTML help builder.
htmlhelp_basename = 'bok-choydoc'

html_theme_options = {
 "repository_url": "https://github.com/openedx/bok-choy",
 "repository_branch": "master",
 "path_to_docs": "docs/",
 "home_page_in_toc": True,
 "use_repository_button": True,
 "use_issues_button": True,
 "use_edit_page_button": True,
 # Please don't change unless you know what you're doing.
 "extra_footer": """
        <a rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
            <img
                alt="Creative Commons License"
                style="border-width:0"
                src="https://i.creativecommons.org/l/by-sa/4.0/80x15.png"/>
        </a>
        <br>
        These works by
            <a
                xmlns:cc="https://creativecommons.org/ns#"
                href="https://openedx.org"
                property="cc:attributionName"
                rel="cc:attributionURL"
            >The Axim Collaborative</a>
        are licensed under a
            <a
                rel="license"
                href="https://creativecommons.org/licenses/by-sa/4.0/"
            >Creative Commons Attribution-ShareAlike 4.0 International License</a>.
    """
}


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'bok-choy.tex', 'bok-choy Documentation',
   author, 'manual'),
]


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'bok-choy', 'bok-choy Documentation',
     [author], 1)
]


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'bok-choy', 'bok-choy Documentation',
   author, 'bok-choy', 'One line description of project.',
   'Miscellaneous'),
]


# -- Autodoc options -----------------------------------------------------------
autoclass_content = 'both'
