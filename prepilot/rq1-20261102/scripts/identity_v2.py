"""RQ1 short-export identity v2: ignore only preamble Date; compare all else."""
from pathlib import Path

def canonical_file(path):
 p=Path(path);s=p.read_text()
 if p.suffix=='.v':
  lines=s.splitlines(keepends=True)
  i=next(i for i,x in enumerate(lines) if x.strip() and not x.lstrip().startswith('//'))
  if not lines[i].startswith('`timescale '):raise ValueError('Unexpected HDL preamble/directive')
  prefix=lines[:i]
  expected='// Command     : write_verilog -force -mode funcsim snapshot_funcsim.v\n'
  if prefix.count(expected)!=1:raise ValueError('Non-v2 or wrapped export command')
  dates=[x for x in prefix if x.startswith('// Date        : ')]
  if len(dates)!=1:raise ValueError('Unexpected generated Date cardinality')
  # Keep every directive, attribute, comment and code line from timescale to EOF.
  # All other preamble text also remains in comparison.
  return ''.join(x for x in prefix if x!=dates[0])+''.join(lines[i:])
 if p.suffix=='.xdc':
  if s.count('# Command Used: write_xdc -force snapshot_constraints.xdc\n')!=1:
   raise ValueError('Non-v2 XDC export command')
  return s  # Entire XDC including comments/commands; no normalization at all.
 raise ValueError('Unsupported identity input')
