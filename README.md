# CodeViz

Visualize code dependencies between files in your __C/C++__ projects.

CodeViz is a simple, cross-platform, python3 script that creates a code
dependency graph using source and header files.

It works by first creating a dot file. The dot file is then then passed into
graphviz, which is a supporting program that will automagically create a map
of your code.


# Installation

`codeviz` requires __graphviz__ installed. Follow the graphviz installation
instructions for your platform:

* [Arch Linux](https://www.archlinux.org/packages/extra/x86_64/graphviz/) (AUR)
* [Fedora](http://www.graphviz.org/download)
* [FreeBSD](https://www.freshports.org/graphics/graphviz)
* [Mac](http://www.graphviz.org/download)
* [Ubuntu/Debian](http://www.graphviz.org/download)
* [Windows](http://graphviz.org/download)
* [Solaris](http://graphviz.org/download)

Once graphviz is installed, ensure that it is available in your environment.

Finally, to install `codeviz` onto your system:

    $ git clone https://github.com/jmarkowski/codeviz.git
    $ cd codeviz
    $ python3 setup.py install


# Example

The image below shows the result of generating the visual code map for the
original git source at hash `e83c516`.

![git e83c516](example.png)


# Usage

Run `codeviz` inside of your source directory. By default, it will only use
the source/header files in the working directory (system header files such as
_stdio.h_ are ignored).

    $ codeviz

You may also search for source/header files recursively as so

    $ codeviz -r

⚠️ Because `codeviz` does not know anything about your include paths, there
may be collisions between connections if there are multiple header files that
share the same filename despite being in separate directories.
`codeviz` will warn you if such collisions occur. ⚠️

If you want a black and white version of the generated dependency graph

    $ codeviz -n

If you would like to ignore source files that are not including the headers you
specify:

    # If a file does not include any of the require*.h headers, it is ignored.
    $ codeviz require*.h -m

You can specify the name of an output file. The extension will be passed into
graphviz to generate the appropriate file.

    $ codeviz -o jpeg-file.jpg
    $ codeviz -o postscript-file.ps
    $ codeviz -o png-file.png

See [here](http://www.graphviz.org/doc/info/output.html) for a complete list
of supported output formats

Finally, can you ignore certain files and directories from being used.

    # Ignore tests
    $ codeviz -r --ignore=unit-tests/* --ignore=test *.{c,cpp,h,hpp}
