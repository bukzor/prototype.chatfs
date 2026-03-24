#!/bin/bash
set -eu
HERE=$(dirname "$0")

set -x
cd "$HERE"
python3 -m http.server
