import argparse
import tabulate

from typing import List
from operator import itemgetter
from bugzoo.manager import BugZoo


def list_sources(rbox: 'BugZoo') -> None:
    """
    Produces a list of all the sources known to BugZoo.
    """
    hdrs = ['Source', 'URL', 'Version']
    tbl = []
    for src in rbox.sources:
        tbl.append([src.name, src.url, src.version])

    # transform into a pretty table
    tbl = tabulate.tabulate(tbl, headers=hdrs, tablefmt='simple')
    print('')
    print(tbl)


def add_source(rbox: 'BugZoo', src: str) -> None:
    rbox.sources.add(src)
    print('added dataset: {}'.format(src))


def remove_source(rbox: 'BugZoo', name: str) -> None:
    rbox.sources.remove_by_name(name)
    print('removed source: {}'.format(name))


def update_sources(rbox: 'BugZoo', ) -> None:
    print('updating sources...')
    rbox.sources.update()


###############################################################################
# [dataset] group
###############################################################################


def list_datasets(rbox: 'BugZoo') -> None:
    tbl = []
    hdrs = ['Dataset', 'Source', '# Bugs']
    for ds in rbox.datasets:
        row = [ds.name, ds.url, ds.size]
        tbl.append(row)

    tbl = sorted(tbl, key=itemgetter(0))

    # transform into a pretty table
    tbl = tabulate.tabulate(tbl, headers=hdrs, tablefmt='simple')
    print('')
    print(tbl)


###############################################################################
# [bug] group
###############################################################################


def validate_bug(rbox: 'BugZoo', name: str, verbose: bool = True) -> None:
    print('validating bug: {}'.format(name))
    bug = rbox.bugs[name]
    if bug.validate(verbose=verbose):
        print('OK')
    else:
        print('FAIL')


def install_bug(rbox: 'BugZoo', name: str, update: bool) -> None:
    print('installing bug: {}'.format(name))
    bug = rbox.bugs[name]
    bug.install(upgrade=update)


def build_bug(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('building bug: {}'.format(name))
    bug = rbox.bugs[name]
    bug.build(force=force)


def download_bug(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('downloading bug: {}'.format(name))
    bug = rbox.bugs[name]
    bug.download(force=force)


def upload_bug(rbox: 'BugZoo', name: str) -> None:
    print('uploading bug: {}'.format(name))
    bug = rbox.bugs[name]
    bug.upload()


def uninstall_bug(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('uninstalling bug: {}'.format(name))
    bug = rbox.bugs[name]
    bug.uninstall(force=force)


def list_bugs(rbox: 'BugZoo', show_installed=None) -> None:
    tbl = []
    hdrs = ['Bug', 'Source', 'Installed?']
    for bug in rbox.bugs:

        # apply filtering based on installation status
        if show_installed is not None:
            if show_installed != bug.installed:
                continue

        installed = 'Yes' if bug.installed else 'No'
        row = [bug.identifier, bug.dataset.name, installed]
        tbl.append(row)

    # sort by dataset then by bug
    tbl = sorted(tbl, key=itemgetter(1,2))

    # transform into a pretty table
    tbl = tabulate.tabulate(tbl, headers=hdrs, tablefmt='simple')
    print('')
    print(tbl)


###############################################################################
# [tool] group
###############################################################################

def install_tool(rbox: 'BugZoo', name: str, update: bool) -> None:
    print('installing tool: {}'.format(name))
    t = rbox.tools[name]
    t.install(upgrade=update)


def uninstall_tool(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('uninstalling tool: {}'.format(name))
    rbox.tools[name].uninstall(force=force)


def build_tool(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('building tool: {}'.format(name))
    rbox.tools[name].build(force=force)


def download_tool(rbox: 'BugZoo', name: str, force: bool) -> None:
    print('downloading tool: {}'.format(name))
    rbox.tools[name].download(force=force)


def upload_tool(rbox: 'BugZoo', name: str) -> None:
    print('uploading tool: {}'.format(name))
    rbox.tools[name].upload()


# TODO: tidy up copypasta
def list_tools(rbox: 'BugZoo', show_installed=None) -> None:
    tbl = []
    hdrs = ['Tool', 'Source', 'Installed?']
    for tool in rbox.tools:

        # apply filtering based on installation status
        if show_installed is not None:
            if show_installed != tool.installed:
                continue

        installed = 'Yes' if tool.installed else 'No'
        row = [tool.name, tool.url, installed]
        tbl.append(row)

    # sort by dataset then by bug
    tbl = sorted(tbl, key=itemgetter(1,2))

    # transform into a pretty table
    tbl = tabulate.tabulate(tbl, headers=hdrs, tablefmt='simple')
    print('')
    print(tbl)


###############################################################################
# [container] group
###############################################################################


def launch(rbox: 'BugZoo', name: str, tools: List[str] = []) -> None:
    bug = rbox.bugs[name]
    bug.install()
    tools = [rbox.tools[t] for t in tools]
    try:
        c = None
        c = bug.provision(tty=True, tools=tools)
        c.interact()
    finally:
        if c: # ensure the container is destroyed
            c.destroy()



def main():
    #with open(os.path.join(os.path.dirname(__file__), "banner.txt"), "r") as f:
    #    desc = f.read()
    rbox = BugZoo()

    desc = ':-)'
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers()
    parser.add_argument('--version', action='version', version='2.0.0')

    ###########################################################################
    # [source] group
    ###########################################################################
    g_src = subparsers.add_parser('source')
    g_subparsers = g_src.add_subparsers()

    # [source list]
    cmd = g_subparsers.add_parser('list')
    cmd.set_defaults(func=lambda args: list_sources(rbox))

    # [source add :dataset]
    cmd = g_subparsers.add_parser('add')
    cmd.add_argument('source')
    cmd.set_defaults(func=lambda args: add_source(rbox, args.source))

    # [source remove :dataset]
    cmd = g_subparsers.add_parser('remove')
    cmd.add_argument('source')
    cmd.set_defaults(func=lambda args: remove_source(rbox, args.source))

    # [source update]
    cmd = g_subparsers.add_parser('update')
    cmd.set_defaults(func=lambda args: update_sources(rbox))


    ###########################################################################
    # [tool] group
    ###########################################################################
    g_tool = subparsers.add_parser('tool')
    g_subparsers = g_tool.add_subparsers()

    # [tool install (--update) :tool]
    cmd = g_subparsers.add_parser('install')
    cmd.add_argument('tool')
    cmd.add_argument('--update',
                     action='store_true')
    cmd.set_defaults(func=lambda args: install_tool(rbox, args.tool, args.update))

    # [tool uninstall (--force) :tool]
    cmd = g_subparsers.add_parser('uninstall')
    cmd.add_argument('tool')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: uninstall_tool(rbox, args.tool, force=args.force))

    # [tool build (--update) :bug]
    cmd = g_subparsers.add_parser('build')
    cmd.add_argument('tool')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: build_tool(rbox, args.tool, args.force))

    # [tool download (--force) :bug]
    cmd = g_subparsers.add_parser('download')
    cmd.add_argument('tool')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: download_tool(rbox, args.tool, args.force))

    # [tool upload :bug]
    cmd = g_subparsers.add_parser('upload')
    cmd.add_argument('tool')
    cmd.set_defaults(func=lambda args: upload_tool(rbox, args.tool))

    # [tool list]
    cmd = g_subparsers.add_parser('list')
    cmd.add_argument('--installed',
                     dest='installed',
                     action='store_true')
    cmd.add_argument('--uninstalled',
                     dest='installed',
                     action='store_false')
    cmd.set_defaults(installed=None)
    cmd.set_defaults(func=lambda args: list_tools(rbox, args.installed))


    ###########################################################################
    # [dataset] group
    ###########################################################################
    g_dataset = subparsers.add_parser('dataset')
    g_subparsers = g_dataset.add_subparsers()

    # [datasetlaunch :bug]
    cmd = g_subparsers.add_parser('list')
    cmd.set_defaults(func=lambda args: list_datasets(rbox))


    ###########################################################################
    # [container] group
    ###########################################################################
    g_container = subparsers.add_parser('container')
    g_subparsers = g_container.add_subparsers()

    # [container launch :bug]
    cmd = g_subparsers.add_parser('launch')
    cmd.add_argument('bug')
    # TODO: add volumes
    cmd.add_argument('--with',
                     help='name of a tool',
                     dest='tools',
                     action='append',
                     default=[])
    cmd.set_defaults(func=lambda args: launch(rbox, args.bug, args.tools))

    # [container run :bug]

    # [container connect :bug]


    ###########################################################################
    # [bug] group
    ###########################################################################
    g_bug = subparsers.add_parser('bug')
    g_subparsers = g_bug.add_subparsers()

    # [bug validate (-v|--verbose) :bug]
    cmd = g_subparsers.add_parser('validate')
    cmd.add_argument('bug')
    cmd.add_argument('-v', '--verbose',
                     action='store_true')
    cmd.set_defaults(func=lambda args: validate_bug(rbox, args.bug, args.verbose))

    # [bug install (--update) :bug]
    cmd = g_subparsers.add_parser('install')
    cmd.add_argument('bug')
    cmd.add_argument('--update',
                     action='store_true')
    cmd.set_defaults(func=lambda args: install_bug(rbox, args.bug, args.update))

    # [bug uninstall (--force) :bug]
    cmd = g_subparsers.add_parser('uninstall')
    cmd.add_argument('bug')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: uninstall_bug(rbox, args.bug, force=args.force))

    # [bug build (--update) :bug]
    cmd = g_subparsers.add_parser('build')
    cmd.add_argument('bug')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: build_bug(rbox, args.bug, args.force))

    # [bug download (--force) :bug]
    cmd = g_subparsers.add_parser('download')
    cmd.add_argument('bug')
    cmd.add_argument('--force',
                     action='store_true')
    cmd.set_defaults(func=lambda args: download_bug(rbox, args.bug, args.force))

    # [bug upload :bug]
    cmd = g_subparsers.add_parser('upload')
    cmd.add_argument('bug')
    cmd.set_defaults(func=lambda args: upload_bug(rbox, args.bug))

    # [bug list]
    cmd = g_subparsers.add_parser('list')
    cmd.add_argument('--installed',
                     dest='installed',
                     action='store_true')
    cmd.add_argument('--uninstalled',
                     dest='installed',
                     action='store_false')
    cmd.set_defaults(installed=None)
    cmd.set_defaults(func=lambda args: list_bugs(rbox, args.installed))


    # parse and process arguments
    try:
        args = parser.parse_args()
        if 'func' in vars(args):
            args.func(args)

    # exit gracefully
    except (KeyboardInterrupt, SystemExit):
        pass

    # pretty-print fatal error messages and log them to file
    except Error as e:
        print(e)

if __name__ == "__main__":
    main()
