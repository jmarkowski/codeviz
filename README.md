# CodeViz

Visualize code dependencies in your __C/C++__ projects.

`codeviz` is a super simple, cross-platform, python script that only uses
built-in libraries to create code dependency graphs of your source files.

It works like this:

1. Find the source files and parse them to get their headers.
2. Create a `dot` file that describes the code graph.
3. Pass the `dot` file into `graphviz`, which will create a visual
   graphic of your code dependencies.


# Installation

## 1. Install Graphviz

`codeviz` uses __graphviz__ to create the visual map.

Follow the graphviz installation instructions for your platform:

* [Arch Linux](https://wiki.archlinux.org/title/Graphviz)
* [Fedora](http://www.graphviz.org/download)
* [FreeBSD](https://www.freshports.org/graphics/graphviz)
* [Mac](http://www.graphviz.org/download)
* [Ubuntu/Debian](http://www.graphviz.org/download)
* [Windows](http://graphviz.org/download)
* [Solaris](http://graphviz.org/download)

Once graphviz is installed, ensure that it is available in your environment.

## 2. Install CodeViz

There are a several ways you can install `codeviz`.

### Option A: In a virtual environment with pip

First, build the distribution package:

    $ git clone https://github.com/jmarkowski/codeviz.git
    $ python setup.py sdist

Next, create and start a virtual environment:

    $ virtualenv pyenv
    $ source pyenv/bin/activate

Finally, install the package:

    $ pip install dist/codeviz*

Now, while in the virtual environment, you'll have the `codeviz` command in your
path.

### Option B: Using setup

To install `codeviz` into your system path:

    $ git clone https://github.com/jmarkowski/codeviz.git
    $ cd codeviz
    $ sudo python3 setup.py install

The generated `install-record.txt` file will list the paths of files that were
installed on your system.

### Option C: Just copying the script to your executable path

For example, if you have `~/bin` mapped to your environment's path:

    $ git clone https://github.com/jmarkowski/codeviz.git
    $ cp codeviz/codeviz.py ~/bin/codeviz


# Example

The image below shows the result of generating the visual code map for the
original git source at hash `e83c516`.

![git e83c516](example.png)


# Usage

## General

Run `codeviz` with a path to your source directory to search for source & header
files in the given path:

    $ codeviz path/to/src

Specify multiple code paths, mixing directories and files:

    $ codeviz path/to/src/subdir1 path/to/src/subdir2 path/to/src/subdir3/*.h

Search directories recursively:

    $ codeviz -r path/to/src

Ignore certain files and directories from being used:

    # Ignore tests
    $ codeviz --ignore=unit-tests/* --ignore=test *.{c,cpp,h,hpp}

Limit the source files to those with certain headers:

    # Any source files that do not include the a.h and b.h headers are ignored.
    $ codeviz *.cpp a.h b.h --must-include


## Style Options

If you want a black and white version of the generated dependency graph:

    $ codeviz --no-color path/to/src


## Format Options

You can specify the name of an output file with a variety of output formats.

    $ codeviz path/to/src -o jpeg-file.jpg
    $ codeviz path/to/src -o postscript-file.ps
    $ codeviz path/to/src -o png-file.png

See [here](http://www.graphviz.org/doc/info/output.html) for a complete list
of supported file formats.


# Limitations

1. System header files (e.g. _stdio.h_) are ignored and not referenced. This is
   intentional as it's presumed that you only care about dependencies of *your*
   source code.

2. Because `codeviz` does not know anything about your build system and it's
   include paths, there may be "dependency collisions" if it finds multiple
   header files in separate directories that share the same filename.
   However, `codeviz` will warn you if such collisions occur and still show
   the dependencies in dotted lines labeled with a `?`. You can resolve these
   collisions yourself by modifying the contents of the outputted `dot` file.

3. For very, very large codebases, the `graphviz` tool may fail to create the
   graphic. In such cases, you're better off specifying a smaller subset of
   paths within the codebase that you're really interested in.
