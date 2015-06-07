import os
import sys
import functools
import subprocess

import click
import yaml


binpath = os.path.dirname(sys.executable)
FABCMD = os.path.join(binpath, 'fab')

pkgpath = os.path.dirname(os.path.abspath(__file__))
FABFILE = os.path.join(pkgpath, 'fabfile.py')


def fab(cmd, *args):
    """Run `cmd` with `args` via the fab command."""
    unicode_args = [unicode(arg) for arg in args]
    full_cmd = [
        FABCMD, '-f', FABFILE,
        '%s:%s' % (cmd, ','.join(unicode_args))
    ]
    return subprocess.call(full_cmd)


def merge_arguments_with_config(part=None, requires=()):
    """A command decorator.

    This decorator let the command prefer the arguments specified
    on command line to the values from the configuration file.
    """
    def get_config_values(config):
        """Get all valid values from the configuration file."""
        try:
            with open(config) as f:
                config_values = yaml.load(f)
        except IOError:
            raise click.UsageError('Could not find the configuration file '
                                   '"%s"!' % config)
        except yaml.scanner.ScannerError:
            raise click.UsageError('Found YAML syntax errors in the '
                                   'configuration file! Please fix them.')
        if config_values is None:
            raise click.UsageError('The configuration file is empty! '
                                   'Please fill in the required values.')
        if not isinstance(config_values, dict):
            raise click.UsageError('Found unexpected values in the '
                                   'configuration file! Please correct them.')
        return config_values

    def wrapper(command):
        @functools.wraps(command)
        def decorator(config, **kwargs):
            arguments = kwargs
            # Update `None` arguments if `config` is specified
            if config is not None:
                config_values = get_config_values(config)
                for arg, value in arguments.iteritems():
                    if value is None:
                        if part:
                            c_part, c_arg = part, arg
                        else:
                            c_part, c_arg = arg.split('_', 1)
                        c_value = config_values.get(c_part, {}).get(c_arg)
                        arguments[arg] = c_value
            # Validate required arguments
            for arg in requires:
                if arguments[arg] is None:
                    raise click.UsageError('Missing argument "%s".None' % arg)
            return command(**arguments)
        return decorator
    return wrapper


@click.group(context_settings={
    'auto_envvar_prefix': 'COOLY'
})
@click.version_option()
def cli():
    """Cooly helps you deploy Python projects."""


@cli.command('archive')
@click.option('-c', '--config', help='The configuration file.')
@click.option('--name', help='The project name.')
@click.option('--repo', help='The repository path (local or remote).')
@click.option('--tree-ish',
              help='The tree or commit to produce an archive for.')
@click.option('--output',
              help='The destination directory to store the archive.')
@merge_arguments_with_config('archive', requires=('name', 'repo'))
def archive(name, repo, tree_ish, output):
    """Archive the package."""
    return fab('archive', name, repo, tree_ish or 'HEAD', output or '/tmp')


@cli.command('build')
@click.option('-c', '--config', help='The configuration file.')
@click.argument('pkg', required=True)
@click.option('--host', help='The hostname of the build server.')
@click.option('--toolbin', help='The bin path of Cooly on the build server.')
@click.option('--output', help='The local folder to store the distribution.')
@click.option('--pre-script', help='The script to run before building.')
@click.option('--post-script', help='The script to run after building.')
@merge_arguments_with_config('build', requires=('host', 'toolbin', 'output'))
def build(pkg, host, toolbin, output, pre_script, post_script):
    """Build the package."""
    return fab('build', pkg, host, toolbin, output, pre_script, post_script)


@cli.command('install')
@click.option('-c', '--config', help='The configuration file.')
@click.argument('dist', required=True)
@click.option('--hosts', help='The server hostname to install on.')
@click.option('--path', help='The installation path on the server.')
@click.option('--pre-command', help='The command to run before installing.')
@click.option('--post-command', help='The command to run after installing.')
@merge_arguments_with_config('install', requires=('hosts', 'path'))
def install(dist, hosts, path, pre_command, post_command):
    """Install the distribution."""
    return fab('install', dist, hosts, path, pre_command, post_command)


@cli.command('deploy')
@click.option('-c', '--config', help='The configuration file.')
@click.option('--archive-name', help='The project name.')
@click.option('--archive-repo', help='The repository path (local or remote).')
@click.option('--archive-tree-ish',
              help='The tree or commit to produce an archive for.')
@click.option('--archive-output',
              help='The destination directory to store the archive.')
@click.option('--build-host', help='The hostname of the build server.')
@click.option('--build-toolbin',
              help='The bin path of Cooly on the build server.')
@click.option('--build-output',
              help='The local folder to store the distribution.')
@click.option('--build-pre-script',
              help='The script to run before building.')
@click.option('--build-post-script',
              help='The script to run after building.')
@click.option('--install-hosts', help='The server hostname to install on.')
@click.option('--install-path', help='The installation path on the server.')
@click.option('--install-pre-command',
              help='The command to run before installing.')
@click.option('--install-post-command',
              help='The command to run after installing.')
@merge_arguments_with_config(requires=(
    'archive_name', 'archive_repo',
    'build_host', 'build_toolbin', 'build_output',
    'install_hosts', 'install_path'
))
def deploy(archive_name, archive_repo, archive_tree_ish,
           archive_output, build_host, build_toolbin, build_output,
           build_pre_script, build_post_script, install_hosts,
           install_path, install_pre_command, install_post_command):
    """Deploy the package."""
    return fab('deploy', archive_name, archive_repo,
               archive_tree_ish or 'HEAD', archive_output or '/tmp',
               build_host, build_toolbin, build_output,
               build_pre_script, build_post_script, install_hosts,
               install_path, install_pre_command, install_post_command)
