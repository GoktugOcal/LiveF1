import sys
from pathlib import Path

sys.path.insert(0, str(Path('..','..').resolve()))

import livef1

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'LiveF1'
copyright = '2024, Göktuğ Öcal'
author = 'Göktuğ Öcal'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    # 'sphinx.ext.napoleon',
    "sphinx_copybutton",
    'numpydoc',
    "sphinx.ext.autosummary",
]
# Automatically generate summary tables
autosummary_generate = True  # Enable autosummary generation
autosummary_imported_members = False  # Skip imported members
autodoc_inherit_docstrings = True
autodoc_class_signature = "mixed"


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'pydata_sphinx_theme'
html_theme = 'sphinx_rtd_theme'
# html_theme = 'furo'
# html_theme = "sphinxawesome_theme"

html_static_path = ['_static']
html_logo = "_static/logo.png"

html_theme_options = {
    'logo_only': True,
    'display_version': False,
    "logo": {"image_dark": "_static/logo.png"},
    # "logo": {
    #     # "text": "LiveF1",  # Optional: Adds text next to the logo
    #     "image_dark": "_static/logo.png"  # Optional: Use a different logo for dark mode
    # },
    # "navbar_start": ["logo"],
    # "navbar_center": ["navbar-nav"],
    # "navbar_end": ["navbar-icon-links"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/your-repo",  # Replace with your GitHub repo URL
            "icon": "fab fa-github",
        },
    ],
    "show_nav_level": 2,  # Adjust depth of sidebar navigation (optional)
}

