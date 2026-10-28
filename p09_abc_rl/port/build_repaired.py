"""Create reviewable patched copies; never modify the pinned upstream snapshots."""
from pathlib import Path
import difflib,json
ROOT=Path(__file__).resolve().parents[1]
CHANGES={
 'cosine_scorer.py':[("trainer = Trainer(preTrainedGraphModel=None)","trainer = Trainer(preTrainedGraphModel=modelPath)")],
 'LogicSynthesisEnv.py':[("while(depth+1 <= self.ep_length):","while(depth+1 < self.ep_length):"),("BERT_MODEL_NAME = 'bert-base-cased'","BERT_MODEL_NAME = os.environ.get('ABC_RL_BERT_PATH', 'bert-base-cased')")],
 'LogicSynthesisPolicy.py':[("import numpy as np","import os\nimport numpy as np"),("BERT_MODEL_NAME = 'bert-base-cased'","BERT_MODEL_NAME = os.environ.get('ABC_RL_BERT_PATH', 'bert-base-cased')"),("bert_model.to('cuda')","bert_model.to(os.environ.get('ABC_RL_DEVICE', 'cpu'))"),("aigEmbedding = torch.round(aigEmbedding,decimals=3)","if not self.training:\n            aigEmbedding = torch.round(aigEmbedding,decimals=3)")],
 'trainer.py':[("device='cuda'","device='cpu'"),("torch.load(self.preTrainedGraphModel),strict=False","torch.load(self.preTrainedGraphModel, map_location=self.device, weights_only=True),strict=True")],
}
def main():
 out=ROOT/'port/repaired';out.mkdir(exist_ok=True)
 diffs=[];manifest={}
 for p in sorted((ROOT/'upstream').glob('*')):
  text=p.read_text();original=text
  for old,new in CHANGES.get(p.name,[]):
   assert old in text,(p,old)
   text=text.replace(old,new)
  (out/p.name).write_text(text)
  diffs.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='upstream/'+p.name,tofile='port/repaired/'+p.name))
  if text!=original: manifest[p.name]=len(CHANGES[p.name])
 (ROOT/'port/repairs.patch').write_text(''.join(diffs))
 (ROOT/'results/repair_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
