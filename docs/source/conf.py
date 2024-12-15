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
    'sphinx.ext.viewcode',
    # 'sphinx.ext.napoleon',
    "sphinx_copybutton",
    'numpydoc',
    "sphinx.ext.autosummary",
    'sphinx.ext.autosectionlabel',
    'sphinx_tabs.tabs'
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
# html_theme = "sphinx_book_theme"
# html_theme = "sphinx_tudelft_theme"
html_theme = "shibuya"

# html_logo = "_static/logo.png"
html_favicon = "_static/favicon.png"

# Select a color scheme for light mode
pygments_style = "xcode"
# Select a different color scheme for dark mode
pygments_style_dark = "monokai"

html_favicon = "_static/favicon.png"
html_static_path = ['_static']
html_theme_options = {
    'logo_only': True,
    'display_version': False,
    # "logo": {
    #     "image_dark": "_static/LiveF1_white.png",
    #     "image_light": "_static/LiveF1_red.png",
    #     },
    "light_logo": "_static/LiveF1_red.png",
    "dark_logo": "_static/LiveF1_white.png",
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/goktugocal/LiveF1",  # Replace with your GitHub repo URL
            "icon": "fab fa-github",
        },
    ],
    "show_nav_level": 2,  # Adjust depth of sidebar navigation (optional)
    "rightsidebar": "true",
    "relbarbgcolor": "black",
    "accent_color": "red",
    "github_url": "https://github.com/goktugocal/livef1",
}

