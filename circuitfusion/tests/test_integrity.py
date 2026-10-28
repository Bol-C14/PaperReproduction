import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'pilot'))
from data import build,check
class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.records,_=build(ROOT/'results/data')
    def reject(self,mutation):
        records=copy.deepcopy(self.records);mutation(records)
        with self.assertRaises((AssertionError,IndexError)):check(records)
    def test_valid_roundtrip(self):check(json.loads(json.dumps(self.records)))
    def test_wrong_pair_rejected(self):self.reject(lambda rs:rs[0]['modality_ids'].update(netlist=rs[1]['sample_id']))
    def test_family_split_reassignment_rejected(self):self.reject(lambda rs:rs[0].update(split='test'))
    def test_duplicate_rejected(self):self.reject(lambda rs:rs.append(copy.deepcopy(rs[0])))
    def test_gate_semantic_corruption_rejected(self):
        def corrupt(rs):rs[0]['netlist']['nodes'][rs[0]['netlist']['outputs'][0]][0]='AND'
        self.reject(corrupt)
    def test_summary_corruption_rejected(self):self.reject(lambda rs:rs[0]['summary'].append('wrong'))
    def test_graph_corruption_rejected(self):self.reject(lambda rs:rs[0]['graph']['nodes'][0].__setitem__(0,'wrong'))
if __name__=='__main__':unittest.main(verbosity=2)
