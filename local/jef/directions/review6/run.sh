#!/bin/zsh
cd /Users/oleg/Documents/elections-research
R=jef/directions/review6
cat $R/FIX.md | claude -p --model opus --output-format json --allowedTools "Read($R/input.json),Read(jef/directions/merge3/translated.json),Read($R/out.json),Write($R/out.json),Edit($R/out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $R/run.log 2>&1
echo done
