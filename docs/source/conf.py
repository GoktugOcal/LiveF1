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
    'sphinx_tabs.tabs',
    'sphinx_design',
    # 'jupyter_sphinx'
    'sphinx_sitemap'
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

html_theme = "shibuya"

html_favicon = "_static/favicon.png"

# Select a color scheme for light mode
pygments_style = "xcode"
# Select a different color scheme for dark mode
pygments_style_dark = "monokai"

html_baseurl = "http://livef1.goktugocal.com"
sitemap_excluded_pages = ["404.html"]
sitemap_url_scheme = "{link}"
html_extra_path = ['_static/robots.txt']

html_favicon = "_static/favicon.png"
html_static_path = ['_static']
html_theme_options = {
    "extrahead": "",
    "show_nav_level": 2,  # Adjust depth of sidebar navigation (optional)
    "rightsidebar": "true",
    "relbarbgcolor": "black",
    # Theming
    "accent_color": "red",
    "light_logo": "_static/LiveF1_red.png",
    "dark_logo": "_static/LiveF1_white.png",
    'logo_only': True,
    'display_version': False,  
    # Navbar things
    "github_url": "https://github.com/goktugocal/livef1",
    "nav_links": [
        {
            "title": "Getting Started",
            "url": "getting_started/index"
        },
        {
            "title": "User Guide",
            "url": "user_guide/index"
        },
        {
            "title": "API Reference",
            "url": "api_reference/index"
        },
        # {
        #     "title": "Sponsor me",
        #     "url": "https://github.com/sponsors/goktugocal"
        # },
    ]
}

html_sidebars = {
  "**": [
    "sidebars/localtoc.html",
    "sidebars/repo-stats.html",
    "sidebars/edit-this-page.html"
  ]
}

html_context = {
    "source_type": "github",
    "source_user": "goktugocal",
    "source_repo": "livef1",
    "source_docs_path": "/docs/source/"
}