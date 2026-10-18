#!/bin/zsh
cd /Users/oleg/Documents/elections-research
M=jef/directions/merge2
cat $M/MERGE2.md | claude -p --model opus --output-format json --allowedTools "Read($M/input.tsv),Read($M/out.json),Edit($M/out.json),Write($M/out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $M/run.log 2>&1
echo done
