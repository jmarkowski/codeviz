#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os
import re
import glob


args = None


SOURCE_EXTENSIONS = ('.c', '.cpp')
HEADER_EXTENSIONS = ('.h', '.hpp')
EXTENSIONS = SOURCE_EXTENSIONS + HEADER_EXTENSIONS


class RetCode():
    OK, ERROR, ARG, WARNING = range(4)


class Error(Exception):
    pass


def print_verbose(string):
    if args.verbose:
        print(string)


def print_error(error):
    print(f'ERROR - {error}')


class Node():
    def __init__(self, filepath):
        self.id = f'"{filepath}"'
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.highlight = False

        if self.filename.endswith(SOURCE_EXTENSIONS):
            self.filetype = 'source'
        elif self.filename.endswith(HEADER_EXTENSIONS):
            self.filetype = 'header'

        self.included_headers = self._get_included_headers()

    def _get_included_headers(self):
        includes_re = re.compile(r'\s*#\s*include\s+["<](?P<file>.+?)[">]')

        with open(self.filepath, 'rt') as f:
            data = f.read()

        # Remove all comments
        data = re.sub(r'/\*.*?\*/', '', data, flags=re.DOTALL)
        data = re.sub(r'//.*', '', data)

        return includes_re.findall(data)

    def __str__(self):
        headers = ', '.join(self.included_headers)
        return f'{self.filename} -> [{headers}]\n'


class Edge():
    def __init__(self, source_node, target_node, collision=False):
        self.source_id = source_node.id
        self.target_id = target_node.id
        self.collision = collision


def bash_cmd(cmd):
    retcode = RetCode.OK

    print_verbose('Command: {}'.format(cmd))
    try:
        out_bytes = subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError as e:
        out_bytes = e.output        # output generated before error
        retcode   = e.returncode
    except FileNotFoundError as e:
        print_error('Failed to run command: {}'.format(cmd))
        print('Install required dependency: graphviz '
              '(http://graphviz.org)')
        retcode = RetCode.ERROR

    if retcode:
        out_text = ''
    else:
        out_text = out_bytes.decode('utf-8')

    return (out_text, retcode)


def find_nodes_that_match_basename(nodes, include_path):
    found_nodes = []

    for n in nodes:
        if n.filename == os.path.basename(include_path):
            found_nodes.append(n)

    return found_nodes


def get_highlighted_files():

    highlight_lst = []

    if args.highlight:
        for x in args.highlight:
            highlight_lst = highlight_lst + glob.glob(x)

    for x in highlight_lst:
        print_verbose('Highlight: %s' % x)

    return highlight_lst


def get_nodes(files):
    global args

    nodes = []

    highlight_lst = get_highlighted_files()

    for f in files:
        n = Node(f)

        if args.must_include:
            # Skip source files that are missing any of the headers
            # from the list of header-based files.
            file_has_no_headers = not n.included_headers
            file_header_in_files = bool(
                [
                    h
                    for h in n.included_headers
                    if h in files
                ]
            )

            if file_has_no_headers or not file_header_in_files:
                continue

        if f in highlight_lst:
            n.highlight = True

        nodes.append(n)

    return nodes


def get_edges(nodes):
    edges = []

    for source in nodes:
        for h in source.included_headers:
            headers = find_nodes_that_match_basename(nodes, h)

            if len(headers) > 1:
                collisions = ', '.join(map(lambda h: h.filepath, headers))
                print(f'Warning: Multiple headers with the same basename found for {source.filepath}:')
                for c in headers:
                    print(f' - {c.filepath}')
                    edges.append(Edge(source, c, collision=True))

            elif len(headers) == 1:
                edges.append(Edge(source, headers[0]))

    return edges


def create_dot_file(nodes, edges):
    filename = '.'.join(args.outfile.split('.')[:-1])

    # Find the node with the longest id length
    w = len(max(nodes, key=lambda n: len(n.id)).id)

    with open('{}.dot'.format(filename), 'wt', encoding='utf-8') as f:
        f.write('digraph codeviz {\n')
        f.write('    splines=true\n') # use splines for arrows
        f.write('    sep="+15,15"\n') # min 25 points of margin
        f.write('    overlap=scalexy\n\n') # scale graph in x/y to stop overlap
        f.write('    node [shape=Mrecord, fontsize=12]\n\n')
        for n in nodes:
            if not args.no_color:
                if n.filetype == 'source':
                    if n.highlight:
                        f.write('    node [fillcolor="#ff9999", style=filled]')
                    else:
                        f.write('    node [fillcolor="#ff9999", style=filled]')
                elif n.filetype == 'header':
                    if n.highlight:
                        f.write('    node [fillcolor="#ccffcc", style=filled]')
                    else:
                        f.write('    node [fillcolor="#ccccff", style=filled]')

            f.write(f' {n.id:<{w}} [label = "{n.filepath}"]\n')

        f.write('\n')
        for e in edges:
            attr = ' [style=dotted, label="?"]' if e.collision else ''
            f.write(f'    {e.source_id:<{w}} -> {e.target_id}{attr}\n')
        f.write('}')


def create_graphic():
    filename = '.'.join(args.outfile.split('.')[:-1])
    fileext  = args.outfile.split('.')[-1]

    cmd = 'dot {}.dot'.format(filename)

    (out_text, retcode) = bash_cmd(cmd)

    if retcode:
        return retcode

    cmd = 'neato -Gstart=5 {}.dot -T{} -o {}' \
                                        .format(filename, fileext, args.outfile)

    (out_text, retcode) = bash_cmd(cmd)

    if out_text:
        print_verbose(out_text)

    if not retcode:
        print('Output dot    : {}.dot'.format(filename))
        print('Output graphic: {}'.format(args.outfile))

    return retcode


def find_files(paths, ignore_lst, recurse=False):
    """
    Find all the source files for the given paths.
    Return a sorted list of all the found files.
    """
    files = set()

    for p in paths:
        if os.path.isfile(p):
            files.add(p)
        elif os.path.isdir(p):
            if recurse:
                for relpath, dirs, filenames in os.walk(p):
                    for f in filenames:
                        full_path = os.path.join(relpath, f).lstrip('./\\')
                        if full_path.endswith(EXTENSIONS) \
                                and full_path not in ignore_lst:
                            files.add(full_path)
            else:
                t = lambda f: f.endswith(EXTENSIONS) and f not in ignore_lst
                found_files = filter(t, os.listdir(p))
                full_paths = map(lambda f: os.path.join(p, f), found_files)
                files.update(full_paths)
        else:
            raise Error(f'Invalid file: {p}')

    return sorted(files)


def get_files_to_ignore(ignore_globs):
    files = set()

    if ignore_globs:
        for g in ignore_globs:
            files.update(glob.glob(g, recursive=True))

    if files:
        print_verbose('Ignore files:\n\t{}'.format('\n\t'.join(sorted(files))))

    return files


def parse_arguments():
    global args

    parser = argparse.ArgumentParser(
              description='Generate a code dependency graph for C/C++ projects')

    parser.add_argument(
        dest='paths',
        metavar='path(s)',
        nargs='*')

    parser.add_argument('--verbose',
        dest='verbose',
        action='store_true',
        help='verbose mode')

    parser.add_argument('-v', '--version',
        dest='version',
        action='store_true',
        help='display version information')

    parser.add_argument('-o', '--outfile',
        dest='outfile',
        action='store',
        default='codeviz.png',
        help='output filename')

    parser.add_argument('-r',
        dest='recursive',
        action='store_true',
        help='recursive scan of .c and .h files')

    parser.add_argument('-n', '--no-color',
        dest='no_color',
        action='store_true',
        help='do not use colors to highlight source and header files')

    parser.add_argument('-m', '--must-include',
        dest='must_include',
        action='store_true',
        help='only show nodes whose includes depend on other nodes')

    parser.add_argument('-i', '--ignore',
        dest='ignore_globs',
        metavar='PATTERN',
        action='append',
        help='ignore files matching glob PATTERN')

    parser.add_argument('-H', '--highlight',
        dest='highlight',
        metavar='PATTERN',
        action='append',
        help='highlight files matching glob PATTERN')

    args = parser.parse_args()


def main():
    parse_arguments()

    if args.version:
        import meta
        print('{} {}'.format('codeviz', meta.__version__))
        return RetCode.OK

    ignore_files = get_files_to_ignore(args.ignore_globs)
    files = find_files(args.paths, ignore_files, recurse=args.recursive)

    print_verbose('Found files:\n\t{}'.format('\n\t'.join(files)))

    nodes = get_nodes(files)

    if len(nodes) == 0:
        print('No source files found.')
        return RetCode.WARNING

    edges = get_edges(nodes)

    create_dot_file(nodes, edges)

    return create_graphic()


if __name__ == '__main__':
    retcode = RetCode.ERROR

    try:
        retcode = main()
    except Error as e:
        print_error(e)

    sys.exit(retcode)
