# -*- coding: utf-8 -*-
import argparse
import os
from traceback import format_exc
from utils.io import exit_with_error, print_error, print_warn
import git
import yaml

args = None
this_dir = os.path.abspath(os.path.dirname(__file__))
repo = git.Repo('.')


def run_git(command):
    if isinstance(command, basestring):
        command = command.split()
    command.insert(0, 'git')
    # print '==>', ' '.join(command)
    try:
        return repo.git.execute(command)
    except git.GitCommandError:
        print_error('Git command failed.\n')
        print_error(format_exc())
        if in_conflict():
            print_warn('You have conflicts that need to be resolved.')
        exit_with_error('Aborting')


def pull():
    run_git('pull --rebase')
    
    
def validate_version_new_name(version):
    try:
        parts = tuple(int(p) for p in version.split('.'))
        if len(parts) < 3:
            exit_with_error('Version number needs at least 3 parts, like 11.22.33')
    except ValueError:
        exit_with_error('Invalid version number: {}', version)


def in_conflict():
    resp = run_git('ls-files --unmerged')
    return len(resp) > 0


def ensure_working_tree_is_clean():
    resp = run_git('rev-list @{u}..')
    if len(resp) > 0:
        exit_with_error('Your {} branch is ahead of the origin remote by {} commits. '
                        'Either push or revert these changes before trying again.', repo.active_branch.name, len(resp))


def ensure_all_branches_are_in_sync():
    for branch in ['develop', 'master', find_current_release_branch(), find_current_uat_branch()]:
        print '    checking out', branch
        repo.branches[branch].checkout()
        assert branch == repo.active_branch.name
        pull()
        ensure_current_branch_not_ahead()


def ensure_current_branch_not_ahead():
    resp = run_git('status -s')
    if len(resp) > 0:
        exit_with_error('Your working directory contains changes. Stash, commit or undo them before retrying.')


def merge_branch(src_branch, dst_branch):
    print '    checking out', dst_branch
    repo.branches[dst_branch].checkout()
    print '    merging', src_branch, 'into', dst_branch
    run_git(['merge', '--no-ff', src_branch])
    run_git('push')


def delete_branch(branch_name):
    # delete local and remote
    print '    deleting local branch ', branch_name
    run_git(['branch', '-d', branch_name])
    print '    deleting remote branch', branch_name
    run_git(['push', 'origin', '--delete', branch_name])


def find_current_uat_branch():
    branches = [b.name for b in repo.branches if b.name.startswith('uat/')]
    if len(branches) != 1:
        exit_with_error('Expected to find exactly one UAT branch but found {}: {}', len(branches), branches)
    return branches[0]


def find_current_release_branch():
    branches = [b.name for b in repo.branches if b.name.startswith('release/')]
    if len(branches) != 1:
        exit_with_error('Expected to find exactly one Release branch but found {}: {}', len(branches), branches)
    return branches[0]


def finish_current_uat_branch():
    print 'Retiring current UAT branch'
    uat_branch = find_current_uat_branch()
    release_branch = find_current_release_branch()
    print '  found uat branch', uat_branch
    print '  found release branch', release_branch
    merge_branch(uat_branch, 'master')
    merge_branch(uat_branch, release_branch)
    delete_branch(uat_branch)


def create_new_versioned_branch(branch_family, source_branch):
    version = find_branch_version(source_branch)
    name = '{}/{}'.format(branch_family, version)
    print '    creating local branch ', name
    repo.create_head(name, commit=source_branch)
    print '    creating remote branch', name
    run_git(['push', '-u', 'origin', name])


def create_new_uat_branch():
    print 'Creating new UAT branch'
    rel_branch = find_current_release_branch()
    create_new_versioned_branch('uat', rel_branch)


def finish_current_release_branch():
    print 'Retiring current Release branch'
    release_branch = find_current_release_branch()
    merge_branch(release_branch, 'develop')
    delete_branch(release_branch)


def create_new_release_branch():
    print 'Creating new Release branch'
    create_new_versioned_branch('release', 'develop')


def update_develop_version(next_version):
    print 'Updating version in develop branch to', next_version
    version_data = read_version_data()
    version_data['number'] = next_version
    write_version_data(version_data)
    repo.index.add(['version.yml'])
    repo.index.commit('Update develop version to {}'.format(next_version))
    run_git('push')


def read_version_data():
    version_file = os.path.join(this_dir, 'version.yml')
    with open(version_file) as vf:
        version_data = yaml.load(vf)
    return version_data


def write_version_data(version_data):
    version_file = os.path.join(this_dir, 'version.yml')
    with open(version_file, 'w') as vf:
        yaml.safe_dump(version_data, vf, default_flow_style=False)


def find_branch_version(branch_name):
    prev_branch = repo.active_branch.name
    if prev_branch != branch_name:
        repo.branches[branch_name].checkout()
    version_data = read_version_data()
    version = version_data['number']
    if prev_branch != branch_name:
        repo.branches[prev_branch].checkout()
    return version


def tag_master_version():
    print 'Tagging master version'
    version = find_branch_version('master')
    print '  tag will be', version
    repo.create_tag(version, repo.branches.master.commit.hexsha)
    run_git(['push', 'origin', version])


def main():
    validate_version_new_name(args.next_dev_version)
    ensure_working_tree_is_clean()
    finish_current_uat_branch()
    tag_master_version()
    create_new_uat_branch()
    finish_current_release_branch()
    create_new_release_branch()
    update_develop_version(args.next_dev_version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform a full release waterfall.')
    parser.add_argument('next_dev_version', help='The next version number to be assigned to the develop branch.', type=str)
    args = parser.parse_args()
    main()