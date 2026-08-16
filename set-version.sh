#!/bin/sh

ver=`grep "VERSION = " src/thunk_gen.py | cut -d "\"" -f 2`
meson rewrite kwargs set project / version $ver
echo $ver
