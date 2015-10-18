import os
import tempfile
import functools
import datetime

from fabric.api import (
    task, settings, lcd, local, cd, run, put, get, execute
)
from fabric.colors import green, yellow


EXT = '.tar.gz'


def pythonic_arguments(task):
    """A decorator that tries to evaluate all meaningful strings to
    Python values.
    """
    def evaluate(string):
        try:
            value = eval(string)
        except Exception:
            value = string
        return value

    @functools.wraps(task)
    def decorator(*args, **kwargs):
        evaluated_args = [evaluate(arg) for arg in args]
        evaluated_kwargs = {
            arg: evaluate(value)
            for arg, value in kwargs.iteritems()
        }
        return task(*evaluated_args, **evaluated_kwargs)
    return decorator


'''
# The following version only works locally.

def get_obsolete_version_names(path, max_versions, excludes=None):
    """Get the names of all obsolete versions in local `path` except the
    names specified in `excludes`. As a result, the number of the
    latest versions in remote `path` is no more than `max_versions`.
    """
    excludes = excludes or []

    candidates = os.listdir(path)
    names = set(candidates) - set(excludes)

    ctime = lambda name: os.stat(os.path.join(path, name)).st_ctime
    sorted_names = sorted(names, key=ctime, reverse=True)

    return sorted_names[max_versions:]
'''


def get_obsolete_version_names(path, max_versions, ignore_pattern=''):
    """Get the names of all obsolete versions in remote `path` except the
    names matching the `ignore_pattern`. As a result, the number of the
    latest versions in remote `path` is no more than `max_versions`.
    """
    # List all names of the entries in `path`
    # Options:
    #     -1: list one file per line
    #     -t: sort by modification time, neweset first
    #     -I PATTERN: do not list implied entries matching shell PATTERN
    ignore_option = '-I %s' % ignore_pattern if ignore_pattern else ''
    result = run('ls -1t %s %s' % (ignore_option, path))

    # Convert the result, a single (likely multiline) string, to a list
    names = result.splitlines()

    return names[max_versions:]


def cp(source, dest):
    """Copy `source` to `dest` locally."""
    local('cp -rf %s %s' % (source, dest))


@task
@pythonic_arguments
def archive(repo, tree_ish, name_format, output):
    """Archive the package."""
    print(yellow('>>> Archive stage.'))

    # Archive local repository
    if repo.startswith('file://'):
        repo_path = repo[len('file://'):]
    # Archive remote repository
    # since `git archive --remote` is not widely supported,
    # we use `git clone` first, and then use `git archive` locally
    else:
        repo_tmp = tempfile.mkdtemp()
        with lcd(repo_tmp):
            local('git clone %s' % repo)
        repo_path = local('ls -d %s/*' % repo_tmp, capture=True)

    # Analyze the package
    setup_py = os.path.join(repo_path, 'setup.py')
    if not os.path.isfile(setup_py):
        raise RuntimeError('No `setup.py` found in the package %r' % repo_path)
    name, version = local('python %s --name --version' % setup_py,
                          capture=True).splitlines()

    pkg_name = '%s%s' % (
        name_format.format(
            name=name,
            version=version,
            tree_ish=tree_ish,
            datetime=datetime.datetime.now()
        ),
        EXT
    )
    pkg = os.path.join(output, pkg_name)
    with lcd(repo_path):
        local('git archive -o "%s" %s' % (pkg, tree_ish))

    # Clean up
    try:
        local('rm -rf %s' % repo_tmp)
    except NameError:
        pass

    print(green('>>> Package %s created!' % pkg))
    return pkg


@task
@pythonic_arguments
def build(pkg, host, toolbin, output, requirements, pre_script, post_script):
    """Build the package."""
    print(yellow('>>> Build stage.'))

    # Remote operations
    if host:
        smart_cd, smart_run, smart_put, smart_get = cd, run, put, get
    # Local operations
    else:
        smart_cd, smart_run, smart_put, smart_get = lcd, local, cp, cp

    with settings(host_string=host):
        # Upload the package
        build_tmp = '/tmp/cooly'
        smart_run('mkdir -p %s' % build_tmp)
        pkg_name = os.path.basename(pkg)
        smart_put(pkg, os.path.join(build_tmp, pkg_name))

        # Build there
        with smart_cd(build_tmp):
            smart_run('tar xzf %s' % pkg_name)
            dist = os.path.join(output, pkg_name)

            build_tool = os.path.join(toolbin, 'platter')
            smart_run('%s build %s %s %s .' % (
                build_tool,
                '--requirements=%s' % requirements if requirements else '',
                '--prebuild-script=%s' % pre_script if pre_script else '',
                '--postbuild-script=%s' % post_script if post_script else ''
            ))

            # Download the distribution
            local('mkdir -p %s' % output)
            smart_get('dist/*%s' % EXT, dist)

        # Clean up
        smart_run('rm -rf %s' % build_tmp)

    print(green('>>> Distribution %s created!' % dist))
    return dist


@task
@pythonic_arguments
def install(dist, hosts, path, pre_command, post_command, max_versions):
    """Install the distribution."""

    def work():
        """The actual installation work."""
        print(yellow('>>> Install stage.'))

        # Run the pre-install command if specified
        if pre_command:
            run(pre_command)

        # Upload the distribution
        install_tmp = '/tmp/cooly'
        run('rm -rf {0} && mkdir -p {0}'.format(install_tmp))
        dist_name = os.path.basename(dist)
        put(dist, os.path.join(install_tmp, dist_name))

        with cd(install_tmp):
            # Extract the distribution, throwing away the toplevel folder
            run('tar --strip-components=1 -xzf %s' % dist_name)

            # Install into a specific directory
            install_path = os.path.join(path, dist_name.rstrip(EXT))
            run('./install.sh %s' % install_path)

            # Create or overwrite the symlink for the newly installed
            # distribution to make it available
            serve_path = os.path.join(path, 'current')
            run('ln -sfn %s %s' % (install_path, serve_path))

        # Run the post-install command if specified
        if post_command:
            run(post_command)

        # Limit the number of the versions if required
        if isinstance(max_versions, int) and max_versions > 0:
            version_names = get_obsolete_version_names(
                path, max_versions,
                ignore_pattern='current'
            )
            if version_names:
                with cd(path):
                    run('rm -rf %s' % ' '.join(version_names))
        else:
            raise RuntimeError('Argument `max_versions` is not a '
                               'positive integer')

        # Clean up
        run('rm -rf %s' % install_tmp)

        print(green('>>> Distribution %s installed!' % dist))

    # Execute the work on multiple hosts (serially, by default)
    host_list = hosts.split(';')
    execute(work, hosts=host_list)


@task
@pythonic_arguments
def deploy(archive_repo, archive_tree_ish, archive_name_format, archive_output,
           build_host, build_toolbin, build_output, build_requirements,
           build_pre_script, build_post_script, install_hosts, install_path,
           install_pre_command, install_post_command, install_max_versions):
    """Deploy the package."""
    pkg = archive(archive_repo, archive_tree_ish, archive_name_format,
                  archive_output)
    dist = build(pkg, build_host, build_toolbin, build_output,
                 build_requirements, build_pre_script, build_post_script)
    install(dist, install_hosts, install_path, install_pre_command,
            install_post_command, install_max_versions)
