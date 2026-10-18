#!/bin/zsh
cd /Users/oleg/Documents/elections-research
M=jef/directions/merge3
cat $M/TRANSLATE.md | claude -p --model opus --output-format json --allowedTools "Read($M/translate_input.tsv),Read($M/translated.json),Write($M/translated.json),Edit($M/translated.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $M/translate.log 2>&1
echo done
