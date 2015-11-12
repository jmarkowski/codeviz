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
        self.name     = self.get_name(filename)
        self.filename = filename
        self.includes = self.get_includes(filename)

    def get_includes(self, filename):
        regexp = re.compile(r'#include ["<](?P<file>[\w\.]+)[">]')
        includes = []
        with open(filename, 'rt') as f:
            for line in f:
                result = regexp.search(line)
                if result:
                    includes.append(result.group('file'))

        return includes

    @staticmethod
    def get_name(filename):
        return re.sub('(-|\.)','', filename)


class Edge():
    def __init__(self, start_node, end_node):
        self.start = start_node.name
        self.end = end_node.name


def bash_cmd(cmd):
    retcode = RetCode.OK

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
        for inc in start_node.includes:
            end_node = find_node(nodes, inc)
            if end_node:
                edges.append(Edge(start_node, end_node))
    return edges


def gen_dot_file(nodes, edges):

    with open('codemap.dot', 'wt', encoding='utf-8') as f:
        #f.write('graph codemap {\n')
        f.write('digraph codemap {\n')
        f.write('    splines=true\n') # use splines for arrows
        f.write('    sep="+25,25"\n') # min 25 points of margin
        f.write('    overlap=scalexy\n') # scale graph in x/y to remove overlap
        #f.write('    ranksep=3\n')
        #f.write('    ratio=auto\n')
        #f.write('   node [shape=box, style=filled]\n')
        for n in nodes:
            f.write('    {} [label = "{}"]\n'.format(n.name, n.filename))

        for e in edges:
            f.write('    {} -> {}\n'.format(e.start, e.end))
        f.write('}')


def gen_graphic():
    #cmd = 'dot -Tpng codemap.dot -o codemap.png'

    cmd = 'dot codemap.dot'

    bash_cmd(cmd)
    file_ext = args.outfile.split('.')[-1]

    cmd = 'neato -Gstart=5 codemap.dot -T{} -o {}' \
                                                 .format(file_ext, args.outfile)

    (out_text, retcode) = bash_cmd(cmd)

    if out_text:
        print(out_text)

    return retcode


def parse_arguments():
    '''
    Hypothetical command-line tool for searching a collection of
    files for one or more text patterns.
    '''
    global args

    parser = argparse.ArgumentParser(
                                 description='Generate a code dependency graph')

    parser.add_argument(
        dest='filenames',
        metavar='filename',
        nargs='*')

    # todo
    parser.add_argument('-v',
        dest='verbose',
        action='store_false',
        help='verbose mode')

    parser.add_argument('-o',
        dest='outfile',
        action='store',
        default='codemap.ps',
        help='output filename')

    # todo
    parser.add_argument('-r',
        dest='recursive',
        action='store_true',
        help='recursive scan of .c and .h files')

    parser.add_argument('-c',
        dest='connect_only',
        action='store_true',
        help='only graph nodes that have connections')

    args = parser.parse_args()


def main():
    global args

    parse_arguments()

    if args.filenames:
        c_files = list(filter(lambda d: d.endswith('.c'), args.filenames))
        h_files = list(filter(lambda d: d.endswith('.h'), args.filenames))
    else:
        c_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.c')]
        h_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.h')]

    files = c_files + h_files

    nodes = []

    for f in files:
        n = Node(f)

        if args.connect_only:
            if not n.includes or not [x for x in n.includes if x in files]:
                print('{} has no includes'.format(n.filename))
                continue

        nodes.append(n)

    edges = get_edges(nodes)

    gen_dot_file(nodes, edges)

    retcode = gen_graphic()

    return retcode


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('\nAborting')
