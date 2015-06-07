import os
import tempfile
import functools
from datetime import datetime

from fabric.api import task, settings, lcd, local, cd, run, put, get
from fabric.colors import green, yellow


def pythonic_arguments(task):
    """Try to evaluate all meaningful strings to Python values."""
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


@task
@pythonic_arguments
def archive(name, repo, tree_ish, output):
    """Archive the package."""
    print(yellow('>>> Archive stage.'))

    repo_location, repo_url = repo.split('@', 1)
    # Archive local repository
    if repo_location == 'local':
        repo_path = repo_url
    # Archive remote repository
    # since `git archive --remote` is not widely supported,
    # we use `git clone` first, and then use `git archive` locally
    elif repo_location == 'remote':
        repo_tmp = tempfile.mkdtemp()
        with lcd(repo_tmp):
            local('git clone %s' % repo_url)
        repo_path = os.path.join(repo_tmp, name)
    else:
        raise RuntimeError('Argument `repo` is not recognized')

    pkg = os.path.join(
        output,
        '%s-%s.tar.gz' % (name, tree_ish)
    )
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
def build(pkg, host, toolbin, output, pre_script, post_script):
    """Build the package."""
    print(yellow('>>> Build stage.'))

    with settings(host_string=host):
        # Upload the package
        build_tmp = '/tmp/cooly'
        run('mkdir -p %s' % build_tmp)
        pkg_name = os.path.basename(pkg)
        put(pkg, '%s/%s' % (build_tmp, pkg_name))

        # Build there
        with cd(build_tmp):
            run('tar xzf %s' % pkg_name)
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            dist = os.path.join(
                output,
                '%s-%s.tar.gz' % (pkg_name.rstrip('.tar.gz'), now)
            )

            build_tool = os.path.join(toolbin, 'platter')
            run('%s build %s %s .' % (
                build_tool,
                '--prebuild-script=%s' % pre_script if pre_script else '',
                '--postbuild-script=%s' % post_script if post_script else ''
            ))

            # Download the distribution
            local('mkdir -p %s' % output)
            get('dist/*.tar.gz', dist)

        # Clean up
        run('rm -rf %s' % build_tmp)

    print(green('>>> Distribution %s created!' % dist))
    return dist


@task
@pythonic_arguments
def install(dist, hosts, path, pre_command, post_command):
    """Install the distribution."""
    print(yellow('>>> Install stage.'))

    with settings(host_string=';'.join(hosts)):
        # Run the pre-install command if specified
        if pre_command:
            run(pre_command)

        # Upload the distribution
        install_tmp = '/tmp/cooly'
        run('rm -rf {0} && mkdir -p {0}'.format(install_tmp))
        dist_name = os.path.basename(dist)
        put(dist, '%s/%s' % (install_tmp, dist_name))

        with cd(install_tmp):
            # Extract the distribution, throwing away the toplevel folder
            run('tar --strip-components=1 -xzf %s' % dist_name)

            # Install into a specific directory
            install_path = os.path.join(path, dist_name.rstrip('.tar.gz'))
            run('./install.sh %s' % install_path)

            # Create or overwrite the symlink for the newly installed
            # distribution to make it available
            serve_path = os.path.join(path, 'current')
            run('ln -sfn %s %s' % (install_path, serve_path))

        # Run the post-install command if specified
        if post_command:
            run(post_command)

        # Clean up
        run('rm -rf %s' % install_tmp)

    print(green('>>> Distribution %s installed!' % dist))


@task
@pythonic_arguments
def deploy(archive_name, archive_repo, archive_tree_ish,
           archive_output, build_host, build_toolbin, build_output,
           build_pre_script, build_post_script, install_hosts,
           install_path, install_pre_command, install_post_command):
    """Deploy the package."""
    pkg = archive(archive_name, archive_repo, archive_tree_ish,
                  archive_output)
    dist = build(pkg, build_host, build_toolbin, build_output,
                 build_pre_script, build_post_script)
    install(dist, install_hosts, install_path,
            install_pre_command, install_post_command)
