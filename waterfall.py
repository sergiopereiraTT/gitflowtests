# -*- coding: utf-8 -*-
import argparse
import os
from utils.io import exit_with_error

args = None
this_dir = os.path.abspath(os.path.dirname(__file__))


def validate_version(version):
    try:
        return tuple(int(p) for p in version.split('.'))
    except ValueError:
        exit_with_error('Invalid version number: {}', version)


def main():
    validate_version(args.next_dev_version)
    # this line pretends to be a hotfix in the uat branch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform a full release waterfall.')
    parser.add_argument('next_dev_version', help='The next version number to be assigned to the develop branch.', type=str)
    args = parser.parse_args()
    main()