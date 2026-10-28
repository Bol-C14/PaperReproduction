"""Apply narrowly scoped repairs to a frozen public-source snapshot."""
from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parent

def patch(path, edits):
    old=(ROOT/'upstream_original'/path).read_text(); new=old
    for before,after,count in edits:
        assert new.count(before)==count,(path,before,new.count(before))
        new=new.replace(before,after)
    (ROOT/'repaired'/path).write_text(new)
    return ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='upstream_original/'+path,tofile='repaired/'+path))

diff=patch('model/ckt_fusion/models/model_pretrain.py',[
 ('        alpha = 0.5\n        alpha = 0.9\n        alpha = 0\n','        alpha = self.config.get("modality_mix_alpha", 0.5)\n',1),
 ('        alpha = 0\n','        alpha = self.config.get("modality_mix_alpha", 0.5)\n',1)])
diff+=patch('data_collect/rtl/rtl2summary/summary2vec.py',[
 ("{design_name}/{ep}.v'","{design_name}/{ep}.txt'",1),
 ('            exit()\n','',1)])
diff+=patch('model/ckt_fusion/pretrain_align_all.py',[
 ("    optimizer = AdamW([",'    batch_counts = [len(loader) for loader in train_loader_align]\n    if not batch_counts or len(set(batch_counts)) != 1 or batch_counts[0] == 0:\n        raise ValueError("Aligned modality loaders must have equal nonzero batch counts")\n    updates_per_epoch = (batch_counts[0] + accumulation_steps - 1) // accumulation_steps\n    optimizer = AdamW([',1),
 ("num_training_steps=config['schedular']['total_updates']*max_epoch",'num_training_steps=updates_per_epoch*max_epoch',1),
 ('        for idx, data in enumerate(zip(', '        num_batches = len(graph_ori_lader_train)\n        optimizer.zero_grad()\n        for idx, data in enumerate(zip(',1),
 ('            accelerator.backward(loss_train)\n            optimizer.step()\n            optimizer.zero_grad()\n            lr_scheduler.step()', '            window_start = (idx // accumulation_steps) * accumulation_steps\n            window_size = min(accumulation_steps, num_batches - window_start)\n            accelerator.backward(loss_train / window_size)',1),
 ('            if (idx+1) % accumulation_steps == 0:', '            if (idx+1) % accumulation_steps == 0 or idx+1 == num_batches:',1),
 ('real_batch_loss/accumulation_steps','real_batch_loss/window_size',1)])
(ROOT/'repairs.patch').write_text(diff)
print(diff)
