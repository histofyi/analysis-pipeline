from flask import render_template


def render(template_name, variables):
    if ".html" not in template_name:
        template_name += ".html"
    return render_template(template_name, **variables)