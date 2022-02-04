from flask import request, render_template
from functools import wraps

import logging


def render(template_name, variables):
    if ".html" not in template_name:
        template_name += ".html"
    return render_template(template_name, **variables)


def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = f"{request.endpoint.replace('.', '/')}.html"
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            else:
                if '/' in template_name:
                    section = template_name.split('/')[0]
                    ctx['nav'] = section
            return render(template_name, ctx)
        return decorated_function
    return decorator
