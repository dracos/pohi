# Configuration file for the Sphinx documentation builder.

import os

# Define the canonical URL if you are using a custom domain on Read the Docs
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    if "html_context" not in globals():
        html_context = {}
    html_context["READTHEDOCS"] = True

# -- Project information

project = 'Searchable transcripts of the Post Office Horizon IT Inquiry hearings'
copyright = 'Crown copyright, OGL v3.0'
author = 'Post Office Horizon IT Inquiry (HTMLized by Matthew Somerville)'

# -- General configuration

extensions = [
    "recommonmark",
    "sphinxcontrib.jquery",
]

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_show_sphinx = False

html_theme_options = {
    'analytics_anonymize_ip': True,
    'logo_only': False,
    'display_version': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#48466d',
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_static_path = ['_static']
html_css_files = ['custom.css', 'lite-yt-embed.css']
html_js_files = ['lite-yt-embed.js']

# -- Options for EPUB output
epub_show_urls = 'footnote'
