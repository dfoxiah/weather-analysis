from jinja2 import Environment
from django.templatetags.static import static
from django.urls import reverse


def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args or None, kwargs=kwargs or None)


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "url": url,
        }
    )
    return env
