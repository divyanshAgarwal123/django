"""Local verification fixture using Django's admin templates and the docs example."""

import re
import sys
import textwrap
from pathlib import Path
from wsgiref.simple_server import make_server

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from django.conf import settings

source = (repo / "docs/ref/contrib/admin/index.txt").read_text()
section = source.split("Color variables\n---------------\n", 1)[1]
match = re.search(r"\.\. code-block:: css\n\n((?:    .*\n|\n)+)", section)
assert match, "The documented CSS example was not found"
example = textwrap.dedent(match[1])

override = """{% extends 'admin/base.html' %}
{% block extrastyle %}{{ block.super }}<style>EXAMPLE</style>{% endblock %}
""".replace("EXAMPLE", example)
preview = """{% extends 'admin/base_site.html' %}{% load static %}
{% block extrastyle %}{{ block.super }}
<link rel="stylesheet" href="{% static 'admin/css/changelists.css' %}">
<link rel="stylesheet" href="{% static 'admin/css/forms.css' %}">
{% endblock %}
{% block content %}
<p>This local fixture renders Django's real admin templates and stylesheets
with the CSS example extracted from ticket #33689's documentation patch.</p>
<h3>Secondary heading</h3>
<p class="help">Secondary help text uses the quiet body color.</p>
<div id="changelist"><table id="result_list">
<thead><tr><th>Example row</th><th>Status</th></tr></thead>
<tbody><tr><th><a href="#">Ordinary item</a></th><td>Visible</td></tr>
<tr class="selected"><th><a href="#">Selected item</a></th><td>Selected</td></tr>
</tbody></table></div>
<div class="submit-row"><input type="button" value="Example button"></div>
{% endblock %}
"""

settings.configure(
    DEBUG=True,
    SECRET_KEY="local-docs-verification-only",
    ALLOWED_HOSTS=["127.0.0.1", "localhost"],
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ],
    STATIC_URL="/static/",
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {
                            "admin/base.html": override,
                            "theme_preview.html": preview,
                        },
                    ),
                    "django.template.loaders.app_directories.Loader",
                ]
            },
        }
    ],
)

import django

django.setup()

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.messages.storage.base import Message
from django.core.wsgi import get_wsgi_application
from django.template.response import TemplateResponse
from django.urls import path, re_path
from django.views.static import serve


def theme_preview(request):
    # A synthetic user/context keeps this rendering fixture free of a database.
    return TemplateResponse(
        request,
        "theme_preview.html",
        {
            "title": "Theme documentation verification",
            "site_title": "Django theme verification",
            "site_header": "Django administration",
            "site_url": "/",
            "has_permission": True,
            "user": User(username="theme-review", is_active=True, is_staff=True),
            "available_apps": [],
            "messages": [
                Message(level, f"{label} message text uses the body foreground.")
                for level, label in [
                    (messages.DEBUG, "Debug"),
                    (messages.INFO, "Information"),
                    (messages.SUCCESS, "Success"),
                    (messages.WARNING, "Warning"),
                    (messages.ERROR, "Error"),
                ]
            ],
        },
    )


urlpatterns = [
    path("", theme_preview),
    path("admin/", admin.site.urls),
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {
            "document_root": repo / "django/contrib/admin/static",
        },
    ),
    re_path(
        r"^docs/(?P<path>.*)$",
        serve,
        {
            "document_root": repo / "docs/_build/html",
        },
    ),
]

if __name__ == "__main__":
    server = make_server("127.0.0.1", 0, get_wsgi_application())
    print(
        f"Serving local admin/docs verification at http://127.0.0.1:{server.server_port}",
        flush=True,
    )
    server.serve_forever()
