#!/bin/zsh
cd /Users/oleg/Documents/elections-research
M=jef/directions/merge
cat $M/MERGE.md | claude -p --model sonnet --output-format json --allowedTools "Read($M/input.tsv),Edit($M/out.json),Read($M/out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $M/run.log 2>&1
echo done
