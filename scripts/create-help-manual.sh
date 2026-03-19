#!/usr/bin/env bash
PATH=".:./target/release/:./target/debug/:$PATH" &&
    matrix-commander-ng --manual >help.manual.txt
echo "help.manual.txt is $(wc -l help.manual.txt | cut -d ' ' -f1) lines long"
