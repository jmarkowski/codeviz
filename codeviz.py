#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os
import re
import glob


SOURCE_EXTENSIONS = ('.c', '.cpp')
HEADER_EXTENSIONS = ('.h', '.hpp')
EXTENSIONS = SOURCE_EXTENSIONS + HEADER_EXTENSIONS


verbose = False


class RetCode():
    OK, ERROR, ARG, WARNING = range(4)


class Error(Exception):
    pass


def print_verbose(string):
    global verbose

    if verbose:
        print(string)


def print_error(error):
    print(f'ERROR - {error}')


class File():
    def __init__(self, filepath):
        self.path = filepath
        self.name = os.path.basename(filepath)

        if filepath.endswith(SOURCE_EXTENSIONS):
            self.type = 'source'
        elif filepath.endswith(HEADER_EXTENSIONS):
            self.type = 'header'

        self.included_headers = self._get_included_headers()

    def _get_included_headers(self):
        includes_re = re.compile(r'\s*#\s*include\s+["<](?P<file>.+?)[">]')

        with open(self.path, 'rt') as f:
            data = f.read()

        # Remove all comments
        data = re.sub(r'/\*.*?\*/', '', data, flags=re.DOTALL)
        data = re.sub(r'//.*', '', data)

        return includes_re.findall(data)


class Node():
    def __init__(self, filepath):
        self.id = f'"{filepath}"'
        self.file = File(filepath)
        self.highlight = False

    def __str__(self):
        headers = ', '.join(self.file.included_headers)
        return f'{self.file.name} -> [{headers}]\n'


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
        if n.file.name == os.path.basename(include_path):
            found_nodes.append(n)

    return found_nodes


def get_nodes(files, highlight_files, force_include=False):
    nodes = []

    for f in files:
        n = Node(f)

        if force_include and n.file.type == 'source':
            # Skip source files that are missing any of the headers
            # from the list of header-based files.
            file_has_no_headers = not n.file.included_headers
            file_header_in_files = bool(
                [
                    h
                    for h in n.file.included_headers
                    if h in files
                ]
            )

            if file_has_no_headers or not file_header_in_files:
                continue

        if f in highlight_files:
            n.highlight = True

        nodes.append(n)

    return nodes


def get_edges(nodes):
    edges = []

    for source in nodes:
        for h in source.file.included_headers:
            headers = find_nodes_that_match_basename(nodes, h)

            if len(headers) > 1:
                collisions = ', '.join(map(lambda h: h.file.path, headers))
                print(f'Warning: Multiple headers with the same basename found for {source.file.path}:')
                for c in headers:
                    print(f' - {c.file.path}')
                    edges.append(Edge(source, c, collision=True))

            elif len(headers) == 1:
                edges.append(Edge(source, headers[0]))

    return edges


def create_dot_file(nodes, edges, output_file, use_colors=True):
    filename, _ = os.path.splitext(output_file)

    # Find the node with the longest id length
    w = len(max(nodes, key=lambda n: len(n.id)).id)

    with open('{}.dot'.format(filename), 'wt', encoding='utf-8') as f:
        f.write('digraph codeviz {\n')
        f.write('    splines=true\n') # use splines for arrows
        f.write('    sep="+15,15"\n') # min 25 points of margin
        f.write('    overlap=scalexy\n\n') # scale graph in x/y to stop overlap
        f.write('    node [shape=Mrecord, fontsize=12]\n\n')
        for n in nodes:
            if use_colors:
                if n.file.type == 'source':
                    if n.highlight:
                        f.write('    node [fillcolor="#ccffcc", style=filled]')
                    else:
                        f.write('    node [fillcolor="#ff9999", style=filled]')
                elif n.file.type == 'header':
                    if n.highlight:
                        f.write('    node [fillcolor="#ccffcc", style=filled]')
                    else:
                        f.write('    node [fillcolor="#ccccff", style=filled]')

            f.write(f'    {n.id:<{w}} [label = "{n.file.path}"]\n')

        f.write('\n')
        for e in edges:
            attr = ' [style=dotted, label="?"]' if e.collision else ''
            f.write(f'    {e.source_id:<{w}} -> {e.target_id}{attr}\n')
        f.write('}')


def create_graphic(output_file):
    filename, ext = os.path.splitext(output_file)

    ext = ext.lstrip('.')

    cmd = f'dot {filename}.dot'

    (out_text, retcode) = bash_cmd(cmd)

    if retcode:
        return retcode

    print('Generated dot file: {}.dot'.format(filename))

    cmd = f'neato -Gstart=5 {filename}.dot -T {ext} -o {output_file}'

    (out_text, retcode) = bash_cmd(cmd)

    if out_text:
        print_verbose(out_text)

    if not retcode:
        print('Generated graph: {}'.format(output_file))

    return retcode


def find_files(paths, ignore_lst, recurse=False):
    """
    Find all the source files for the given paths.
    Return a sorted list of all the found files.
    """
    files = set()

    for p in paths:
        if os.path.isfile(p):
            if p not in ignore_lst:
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


def get_files_matching_pattern(glob_pattern):
    files = set()

    if glob_pattern:
        for g in glob_pattern:
            files.update(glob.glob(g, recursive=True))

    return files


def parse_arguments():
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
        dest='highlight_globs',
        metavar='PATTERN',
        action='append',
        help='highlight files matching glob PATTERN')

    return parser.parse_args()


def main():
    global verbose

    args = parse_arguments()

    if args.version:
        import meta
        print('{} {}'.format('codeviz', meta.__version__))
        return RetCode.OK

    verbose = args.verbose

    ignore_files = get_files_matching_pattern(args.ignore_globs)

    if ignore_files:
        ignore_files_str = '\n\t'.join(sorted(ignore_files))
        print_verbose(f'Ignore files:\n\t{ignore_files_str}')

    files = find_files(args.paths, ignore_files, recurse=args.recursive)

    print_verbose('Found files:\n\t{}'.format('\n\t'.join(files)))

    highlight_files = get_files_matching_pattern(args.highlight_globs)

    nodes = get_nodes(files, highlight_files, force_include=args.must_include)

    if len(nodes) == 0:
        print('No source files found.')
        return RetCode.WARNING

    edges = get_edges(nodes)

    create_dot_file(nodes, edges, args.outfile, use_colors=not args.no_color)

    return create_graphic(args.outfile)


if __name__ == '__main__':
    retcode = RetCode.ERROR

    try:
        retcode = main()
    except Error as e:
        print_error(e)

    sys.exit(retcode)
