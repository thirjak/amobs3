#! /usr/bin/env python3.4
import sys
import codecs
import re

f = open(sys.argv[1], encoding='windows-1252')
o = open("normalized_output.txt", 'w')

for line in f:
# line = re.sub('\n','',line)
# line = line.split('\t')
    #str(line).decode('windows-1252', 'replace').encode('utf-8');
    #codecs.decode(line, 'utf-8').encode('utf-8')
    
    #line = line.replace('^\s*\|-;', '')
    line = re.sub(r'^\s*\|-;', '', line)
    line = re.sub('\s*\|-' ,'--', line)
    o.write(line)
    
f.close()
o.close() 
