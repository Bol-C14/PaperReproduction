"""Reproduce pinned abc_py cache contamination without objective evaluation.

48 successful native reads; do not overlap ABC contexts (ABC is global).
"""
import argparse
import json
from pathlib import Path
import abc_py

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert not args.output.exists()
protocol = json.loads(args.protocol.read_text())
names = protocol['source_train_bank'] + protocol['circuits']


def graph(api, name):
    api.read(str(args.root/'assets/abc-rl'/(name+'.aig')))
    count = api.numNodes()
    edges, bad = [], []
    for i in range(count):
        node = api.aigNode(i)
        for present, get in [(node.hasFanin0,node.fanin0),(node.hasFanin1,node.fanin1)]:
            if present():
                target = get()
                edges.append((i,target))
                if target >= count:
                    bad.append((i,target,node.nodeType()))
    return dict(nodes=count,edges=len(edges),out_of_range=bad),edges


shared = abc_py.AbcInterface()
shared.start()
old = {name:graph(shared,name) for name in names}
shared.end()
rows = []
for name in names:
    fresh = abc_py.AbcInterface()
    fresh.start()
    new, new_edges = graph(fresh,name)
    fresh.end()
    previous, previous_edges = old[name]
    assert not new['out_of_range']
    rows.append(dict(circuit=name,shared=previous,fresh=new,same_edges=previous_edges==new_edges))
args.output.write_text(json.dumps(dict(graph_reads=48,rows=rows),indent=2)+'\n')
