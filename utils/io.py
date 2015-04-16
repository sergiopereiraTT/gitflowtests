# -*- coding: utf-8 -*-
import os
import sys
import platform
from termcolor import cprint


def _get_boolean_env(env_var_name, default=False):
    """Values like "yes"/"no", "true"/"false", "1"/"0", "y"/"n", "t"/"f" (case insensitive) are accepted. Unrecognized
    values will return the default (parameter).
    """
    def_val = 't' if default else 'f'
    value = os.environ.get(env_var_name, def_val).lower()[:1]
    return (not default and value in ['y', '1', 't']) or (default and value not in ['n', '0', 'f'])


def color_output_supported():
    allow_color = not _get_boolean_env('NO_COLOR_OUTPUT')
    return allow_color and not platform.system().lower().startswith('windows')


def print_error(message, *args, **kwargs):
    print_in_color(message, 'red', *args, **kwargs)


def print_warn(message, *args, **kwargs):
    print_in_color(message, 'yellow', *args, **kwargs)


def print_in_color(message, color, *args, **kwargs):
    if color_output_supported():
        cprint(message.format(*args), color, **kwargs)
    else:
        print message.format(*args)


def exit_with_error(message, *args, **kwargs):
    exit_code = kwargs.pop('exit_code', 1)
    print_error(message, *args, **kwargs)
    sys.exit(exit_code)