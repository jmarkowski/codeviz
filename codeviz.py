#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os
import re
import glob


args = None


class RetCode():
    OK, ERROR, ARG, WARNING = range(4)


class Node():
    def __init__(self, filename):
        self.name      = '"{}"'.format(filename)
        self.filename  = filename
        self.includes  = self.get_includes(filename)
        self.highlight = False

        if filename.endswith('.c') or filename.endswith('.cpp'):
            self.filetype = 'source'
        elif filename.endswith('.h') or filename.endswith('.hpp'):
            self.filetype = 'header'

    def get_includes(self, filename):
        includes_re = re.compile(r'\s*#\s*include\s+["<](?P<file>.+?)[">]')

        with open(filename, 'rt') as f:
            data = f.read()

        # Remove all comments
        data = re.sub(r'/\*.*?\*/', '', data, flags=re.DOTALL)
        data = re.sub(r'//.*', '', data)

        includes = includes_re.findall(data)

        return includes

    def __str__(self):
        s = '{:<20s}-> {}'.format(self.filename, ', '.join(self.includes))
        return s


class Edge():
    def __init__(self, start_node, end_node):
        self.start = start_node.name
        self.end = end_node.name


def print_verbose(string):
    if args.verbose:
        print(string)


def bash_cmd(cmd):
    retcode = RetCode.OK

    print_verbose('Command: {}'.format(cmd))
    try:
        out_bytes = subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError as e:
        out_bytes = e.output        # output generated before error
        retcode   = e.returncode
    except FileNotFoundError as e:
        print('Failed to run command: {}'.format(cmd))
        print('Install graphviz '
              '(http://graphviz.org)')
        retcode = RetCode.ERROR

    if retcode:
        out_text = ''
    else:
        out_text = out_bytes.decode('utf-8')

    return (out_text, retcode)


def find_node(nodes, filename):
    for n in nodes:
        if n.filename == filename:
            return n
    return None


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
        print_verbose(n)

        if args.must_include:
            if not n.includes or not [x for x in n.includes if x in files]:
                continue

        if f in highlight_lst:
            n.highlight = True

        nodes.append(n)

    return nodes


def get_edges(nodes):
    edges = []

    for start_node in nodes:
        for include_file in start_node.includes:
            end_node = find_node(nodes, include_file)
            if end_node:
                edges.append(Edge(start_node, end_node))

    return edges


def create_dot_file(nodes, edges):
    filename = '.'.join(args.outfile.split('.')[:-1])

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

            f.write(' {:<20s} [label = "{}"]\n'.format(n.name, n.filename))

        f.write('\n')
        for e in edges:
            f.write('    {:<20s} -> {:>20s}\n'.format(e.start, e.end))
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


def get_files(ext_tpl):
    '''
    Find all the source/header files in the current directory. Return a
    sorted list of all the found files.
    '''
    files_lst = []
    ignore_lst = []

    if args.ignore:
        for x in args.ignore:
            ignore_lst.extend(glob.glob(x))
            print_verbose('Ignored: {}'.format(x))

    if args.recursive:
        for relpath, dirs, files in os.walk('.'):
            for f in files:
                full_path = os.path.join(relpath, f).lstrip('./\\')
                if full_path.endswith(ext_tpl) and full_path not in ignore_lst:
                    files_lst.append(full_path)
    else:
        if args.filenames:
            # Use the files passed in as arguments
            files_lst = list(filter( \
                       lambda d: d.endswith(ext_tpl) and d not in ignore_lst, \
                       args.filenames))
        else:
            # Use only the files in the current working directory
            files_lst = [f for f in os.listdir('.') if f.endswith(ext_tpl) \
                                                       and f not in ignore_lst]

    files_lst.sort()

    return files_lst


def parse_arguments():
    global args

    parser = argparse.ArgumentParser(
              description='Generate a code dependency graph for C/C++ projects')

    parser.add_argument(
        dest='filenames',
        metavar='filename',
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
        dest='ignore',
        action='append',
        help='ignore files matching PATTERN')

    parser.add_argument('-H', '--highlight',
        dest='highlight',
        action='append',
        help='highlight files matching PATTERN')

    args = parser.parse_args()


def main():
    parse_arguments()

    if args.version:
        import meta
        print('{} {}'.format('codeviz', meta.__version__))
        return RetCode.OK

    valid_exts = ('.c', '.h', '.cpp', '.hpp')

    files = get_files(valid_exts)
    nodes = get_nodes(files)
    edges = get_edges(nodes)

    create_dot_file(nodes, edges)

    retcode = create_graphic()

    return retcode


if __name__ == '__main__':
    main()
