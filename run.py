#!/usr/bin/env python
"""

 Run Xash

"""
import os
import sys


def main():
    here = os.path.abspath(os.path.split(__file__)[0])
    libs = [here, os.path.join(here, "tdgl3")]
    sys.path[:0] = libs
    import xash.main
    xash.main.main()

if __name__ == '__main__':
    main()
