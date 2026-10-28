"""OFFLINE transport/schema fixtures; no model outputs or network calls."""
import json,urllib.request
from api_controller import OpenAICompatibleController,validate,parse_json,credential_presence,CU_FIELDS
def prohibited(*a,**k):raise AssertionError('Network must not run in offline tests')
urllib.request.urlopen=prohibited
env={'PAPER_LLM_BASE_URL':'https://stub.invalid/v1','PAPER_LLM_API_KEY':'synthetic-test-placeholder','PAPER_LLM_MODEL':'offline-stub'}
cases=[]
def expect_error(name,callback):
 try:callback()
 except (ValueError,RuntimeError):cases.append({'name':name,'passed':True})
 else:raise AssertionError(name)
expect_error('default unauthorized',lambda:OpenAICompatibleController(environ=env).call(stage='inner_iteration',messages=[{'role':'user','content':'offline'}],max_tokens=256))
expect_error('designated vars absent',lambda:OpenAICompatibleController(environ={},authorized=True).call(stage='inner_iteration',messages=[{'role':'user','content':'offline'}],max_tokens=256))
decision={'action':'search','method':'bayesian','n_samples':12,'parameters':{},'reasoning':'Synthetic offline fixture only'}
def stub(url,data,headers,timeout):
 assert url=='https://stub.invalid/v1/chat/completions'
 assert timeout==180
 assert json.loads(data)['model']=='offline-stub'
 return {'choices':[{'message':{'content':json.dumps(decision)}}]}
client=OpenAICompatibleController(transport=stub,environ=env,authorized=True,max_calls=1)
assert client.call(stage='inner_iteration',messages=[{'role':'user','content':'Synthetic stub fixture'}],max_tokens=256)==decision
cases.append({'name':'offline valid stub dispatch','passed':True})
expect_error('call budget enforced',lambda:client.call(stage='inner_iteration',messages=[{'role':'user','content':'stub'}],max_tokens=256))
expect_error('invalid CU',lambda:validate('circuit_understanding',{}))
assert validate('circuit_understanding',{k:'synthetic fixture' for k in CU_FIELDS})
for name,val in [('invented value',2.53),('boolean value',True)]:
 expect_error(name,lambda val=val:validate('initial_search_space',{'optimization_configuration':{'variables_to_optimize':{'W_pmos_base':{'search_space':[val]}},'variables_fixed':{'W_nmos_base':{'fixed_value':1.68}}}}))
expect_error('over budget batch',lambda:validate('inner_iteration',decision|{'n_samples':13},remaining=12))
expect_error('unsupported parameter override',lambda:validate('inner_iteration',decision|{'parameters':{'beta':4}}))
assert parse_json('```json\n{"ok":true}\n```')=={'ok':True}
print(json.dumps({'kind':'OFFLINE_SYNTHETIC_TESTS_NOT_MODEL_RESULTS','passed':True,'checks':cases,'real_api_calls':0,'model_loads':0},indent=2))
