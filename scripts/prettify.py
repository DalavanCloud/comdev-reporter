#!/usr/bin/env python
# Prettify input json file: indent, sort
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--nosort", action='store_true', help="Don't sort the output", default=False)
parser.add_argument("--clobber",action='store_true', help="Overwrite the input file", default=False)
parser.add_argument("--indent", type=int, help="Indentation to use for the output file (default 1)", default=1)
parser.add_argument("file", help="Input file(s) - omit to use as filter", nargs='*')
args = parser.parse_args()

sorted = "unsorted" if args.nosort else "sorted"

import sys
# Any files provided?
if len(args.file) > 0:
  if sys.hexversion < 0x030000F0:
    print("Using Python2 (adds trailing spaces), output will be " + sorted + ". Indent = " + str(args.indent))
  else:
    print("Using Python3 (strips trailing spaces), output will be " + sorted + ". Indent = " + str(args.indent))
import json

sort_keys = not args.nosort

for arg in args.file:
    print("Reading " + arg)
    input = {}
    try:
        with open(arg, "rb") as f:
            input = json.loads(f.read().decode('UTF-8', errors='replace'))
        out = arg if args.clobber else arg + ".out"
        print("Writing " + out)
        with open(out, "w") as f:
            json.dump(input, f, indent=args.indent, sort_keys=sort_keys)
     # we catch exception so can continue to process other files
    except Exception as ex:
        print(ex)

# No inout files provided
if len(args.file) == 0:
    input = json.loads(sys.stdin.read())
    json.dump(input, sys.stdout, indent=args.indent, sort_keys=sort_keys)
