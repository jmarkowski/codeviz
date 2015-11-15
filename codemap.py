#!/usr/bin/env python3

import sys
import subprocess
import argparse
import os
import re


args = None


class RetCode():
    OK, ERROR, ARG, WARNING = range(4)


class Node():
    def __init__(self, filename):
        self.name     = '"{}"'.format(filename)
        self.filename = filename
        self.includes = self.get_includes(filename)

        if filename.endswith('.c') or filename.endswith('.cpp'):
            self.filetype = 'source'
        elif filename.endswith('.h'):
            self.filetype = 'header'

    def get_includes(self, filename):
        includes_re = re.compile(r'#include[\s]?["<]+(?P<file>[\w\.]+)[">]+')

        with open(filename, 'rt') as f:
            data = f.read()

        # Remove all comments
        data = re.sub(r'/\*.*?\*/', '', data, re.DOTALL)

        includes = includes_re.findall(data)

        return includes

    def __str__(self):
        s = '{:<20s}-> {}'.format(self.filename, ', '.join(self.includes))
        return s


class Edge():
    def __init__(self, start_node, end_node):
        self.start = start_node.name
        self.end = end_node.name


def printVerbose(string):
    if args.verbose:
        print(string)


def bash_cmd(cmd):
    retcode = RetCode.OK

    printVerbose('{:<20s} : {}'.format('command', cmd))
    try:
        out_bytes = subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError as e:
        out_bytes = e.output        # output generated before error
        retcode   = e.returncode

    out_text = out_bytes.decode('utf-8')

    return (out_text, retcode)


def find_node(nodes, filename):
    for n in nodes:
        if n.filename == filename:
            return n
    return None


def get_edges(nodes):
    edges = []
    for start_node in nodes:
        for include_file in start_node.includes:
            end_node = find_node(nodes, include_file)
            if end_node:
                edges.append(Edge(start_node, end_node))
    return edges


def gen_dot_file(nodes, edges):
    filename = '.'.join(args.outfile.split('.')[:-1])

    with open('{}.dot'.format(filename), 'wt', encoding='utf-8') as f:
        #f.write('graph codemap {\n')
        f.write('digraph codemap {\n')
        f.write('    splines=true\n') # use splines for arrows
        f.write('    sep="+15,15"\n') # min 25 points of margin
        f.write('    overlap=scalexy\n\n') # scale graph in x/y to stop overlap
        f.write('    node [shape=Mrecord, fontsize=12]\n\n')
        for n in nodes:
            if not args.no_color:
                if n.filetype == 'source':
                    f.write('    node [fillcolor="#ff9999", style=filled]')
                elif n.filetype == 'header':
                    f.write('    node [fillcolor="#ccccff", style=filled]')
            f.write(' {:<20s} [label = "{}"]\n'.format(n.name, n.filename))

        f.write('\n')
        for e in edges:
            f.write('    {} -> {}\n'.format(e.start, e.end))
        f.write('}')


def gen_graphic():
    #cmd = 'dot -Tpng codemap.dot -o codemap.png'
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
        printVerbose(out_text)

    return retcode


def parse_arguments():
    global args

    parser = argparse.ArgumentParser(
                                 description='Generate a code dependency graph')

    parser.add_argument(
        dest='filenames',
        metavar='filename',
        nargs='*')

    parser.add_argument('-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='verbose mode')

    parser.add_argument('-o', '--outfile',
        dest='outfile',
        action='store',
        default='codemap.png',
        help='output filename')

    # todo
    # parser.add_argument('-r',
    #     dest='recursive',
    #     action='store_true',
    #     help='recursive scan of .c and .h files')

    parser.add_argument('-n', '--no-color',
        dest='no_color',
        action='store_true',
        help='do not use colors to highlight source and header files')

    parser.add_argument('-m', '--must-include',
        dest='must_include',
        action='store_true',
        help='only show nodes whose includes depend on other nodes')

    args = parser.parse_args()


def main():
    global args

    parse_arguments()

    valid_exts = ('.c', '.h', '.cpp')

    if args.filenames:
        files = list(filter(lambda d: d.endswith(valid_exts), args.filenames))
    else:
        files = [f for f in os.listdir(os.getcwd()) if f.endswith(valid_exts)]

    files.sort()

    nodes = []

    for f in files:
        n = Node(f)
        printVerbose(n)

        if args.must_include:
            if not n.includes or not [x for x in n.includes if x in files]:
                continue

        nodes.append(n)

    edges = get_edges(nodes)

    gen_dot_file(nodes, edges)

    retcode = gen_graphic()

    return retcode


if __name__ == '__main__':
    try:
        retcode = main()
        sys.exit(retcode)
    except KeyboardInterrupt as e:
        print('\nAborting')
