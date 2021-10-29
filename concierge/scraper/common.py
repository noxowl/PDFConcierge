import os

import jinja2
import pathlib


def exclude_from_history(tasks, history) -> list:
    try:
        return list(set(tasks) - set(history))
    except TypeError:
        return []


template_path = os.path.join(pathlib.Path(__file__).parent.parent.resolve(), 'templates')
template_loader = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=template_path))
