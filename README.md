# CodeViz

Visualize code dependencies between files in your __C/C++__ projects.

CodeViz is a simple, cross-platform, python3 script that creates a code
dependency graph using source and header files.

It works by first creating a dot file. The dot file is then then passed into
graphviz, which is a supporting program that will automagically create a map
of your code.


# Installation

You will need to have a [python3](http://www.python.org) interpreter installed
to run the script.

Also, the script itself _requires_ __graphviz__ installed. Follow the install
instructions from the graphviz website for your platform:

* [fedora](http://www.graphviz.org/Download_linux_fedora.php)
* [mac OSX](http://www.graphviz.org/Download_macos.php)
* [ubuntu/debian](http://www.graphviz.org/Download_linux_ubuntu.php)
* [windows](http://graphviz.org/Download_windows.php)
* [archlinux](https://www.archlinux.org/packages/extra/x86_64/graphviz/files/) (AUR)

Once installed, make sure that you have these tools in your environment path.


# Example

The image below shows the result of generating the visual code map for the
original git source at hash e83c516.

![git e83c516](example.png)


# Usage

Run `codeviz.py` inside of your source directory. By default, it will only use
the source/header files in the working directory (system header files such as
_stdio.h_ are ignored).

```
codeviz.py
```

You may also search for source/header files recursively as so

```
codeviz.py -r
```

If you want a black and white version of the generated dependency graph

```
codeviz.py -n
```

What if you want a black and white version of the generated dependency
graph, AND you would like to ignore files that are not including any other header
in your source files?

```
codeviz.py -m
```

You can specify the name of an output file. The extension will be passed into
graphviz to generate the appropriate file.

```
codeviz.py -o jpeg-file.jpg
codeviz.py -o postscript-file.ps
codeviz.py -o png-file.png
```

See [here](http://www.graphviz.org/doc/info/output.html) for a complete list
of supported output formats

Finally, can you exclude certain files and directories from being used.

```
codeviz.py -r --exclude=unit-tests/* --exclude=test *.[ch]   # exclude tests
```
