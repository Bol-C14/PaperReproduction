"""Train-only retrieval from externally produced, provenance-tagged graph embeddings.

Does not generate embeddings or claim that synthetic vectors are learned features.
"""
import argparse,json,pathlib
from mechanism import nearest_distance,guidance_exponent

def retrieve(query,bank):
 for key in ('checkpoint_sha256','encoder_id'):
  if query[key]!=bank[key]: raise ValueError('query/bank '+key+' mismatch')
 names=bank['training_designs'];rows=bank['embeddings']
 if len(names)!=len(set(names)) or set(rows)!=set(names):
  raise ValueError('bank must contain exactly the declared training designs')
 if query['design'] in bank.get('heldout_designs',[]) and query['design'] in names:
  raise ValueError('held-out design leaked into training bank')
 if set(names)&set(bank.get('heldout_designs',[])):
  raise ValueError('held-out design leaked into training bank')
 d=nearest_distance(query['embedding'],[rows[n] for n in names])
 return {'design':query['design'],'cosine_distance':d,
         'guidance_exponent_beta':guidance_exponent(d,bank['threshold'],bank['scaling']),
         'checkpoint_sha256':bank['checkpoint_sha256'],'encoder_id':bank['encoder_id'],
         'training_bank_size':len(rows),'inference_status':'supplied_embedding_only_not_policy_inference'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--query',type=pathlib.Path,required=True);ap.add_argument('--bank',type=pathlib.Path,required=True)
 a=ap.parse_args();print(json.dumps(retrieve(json.loads(a.query.read_text()),json.loads(a.bank.read_text())),indent=2))
