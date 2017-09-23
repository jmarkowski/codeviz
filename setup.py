# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='codeviz',
    version='0.1.0',
    description='Create visual code dependency graphs for C/C++ projects',
    long_description=long_description,
    url='https://github.com/jmarkowski/codeviz',
    author='Jan Markowski',
    author_email='jan@markowski.ca',
    license='MIT',
    py_modules=['codeviz'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    entry_points={
        'console_scripts': [
            'codeviz=codeviz:main',
        ],
    },
)
