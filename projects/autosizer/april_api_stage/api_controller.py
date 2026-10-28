"""OpenAI-compatible AutoSizer transport. No network calls on import or in offline tests."""
import json,os,urllib.request,urllib.error
from pathlib import Path

ENV_NAMES=('PAPER_LLM_BASE_URL','PAPER_LLM_API_KEY','PAPER_LLM_MODEL')
CU_FIELDS=('circuit_topology_overview','optimization_variables_mapping',
           'optimization_variables_impact','variable_interactions','key_insights_for_optimization')

def credential_presence(environ=None):
    env=os.environ if environ is None else environ
    return {key:bool(env.get(key)) for key in ENV_NAMES}

def parse_json(text):
    text=text.strip()
    if text.startswith('```'):
        lines=text.splitlines()
        if lines[-1].strip()!='```':raise ValueError('Unclosed JSON fence')
        text='\n'.join(lines[1:-1])
    value=json.loads(text)
    if not isinstance(value,dict):raise ValueError('Response must be a JSON object')
    return value

def validate(stage,value,variables=('W_pmos_base','W_nmos_base'),
             allowed=(.84,1.05,1.26,1.47,1.68,1.89,2.1,2.31,2.52),remaining=12):
    if not isinstance(value,dict):raise ValueError('JSON object required')
    if stage=='circuit_understanding':
        if not all(value.get(k) for k in CU_FIELDS):raise ValueError('Missing or empty circuit-understanding field')
    elif stage=='inner_iteration':
        if value.get('action')=='stop':return value
        if value.get('action')!='search' or value.get('method') not in ('random','bayesian'):raise ValueError('Unsupported action or method')
        n=value.get('n_samples')
        if type(n) is not int or not 1<=n<=remaining:raise ValueError('Invalid attempted-candidate count')
        if value.get('parameters',{})!={}:raise ValueError('Parameter overrides unsupported')
        if not isinstance(value.get('reasoning'),str) or not value['reasoning'].strip():raise ValueError('Decision reasoning required')
    elif stage in ('initial_search_space','outer_regeneration'):
        cfg=value.get('optimization_configuration',{}); active=cfg.get('variables_to_optimize',{}); fixed=cfg.get('variables_fixed',{})
        if not isinstance(active,dict) or not isinstance(fixed,dict):raise ValueError('Variable maps required')
        if set(active)&set(fixed) or set(active)|set(fixed)!=set(variables):raise ValueError('Each variable must be covered exactly once')
        for info in active.values():
            choices=info.get('search_space') if isinstance(info,dict) else None
            if not isinstance(choices,list) or not choices or any(type(x) not in (int,float) or x not in allowed for x in choices) or len(set(choices))!=len(choices):raise ValueError('Invalid or invented active domain')
        for info in fixed.values():
            choice=info.get('fixed_value') if isinstance(info,dict) else info
            if type(choice) not in (int,float) or choice not in allowed:raise ValueError('Invalid or invented fixed value')
    else:raise ValueError('Unsupported stage')
    return value

class OpenAICompatibleController:
    """Caller must supply separately authorized public messages and explicit authorization.
    Credentials are read only from designated runtime variables and never returned/logged.
    max_calls counts failed transport attempts too; retries are caller-controlled.
    """
    def __init__(self, *, transport=None, environ=None, authorized=False, max_calls=10):
        self._env=os.environ if environ is None else environ
        self._transport=transport; self.authorized=authorized; self.max_calls=max_calls; self.calls=0

    def call(self, *, stage, messages, max_tokens, remaining=12, evidence_dir=None):
        if not self.authorized:raise RuntimeError('API execution pending endpoint, credential and public-data authorization')
        if not all(credential_presence(self._env).values()):raise RuntimeError('Required designated API runtime variables are absent')
        if self.calls>=self.max_calls:raise RuntimeError('API attempted-call budget exhausted')
        caps={'circuit_understanding':1536,'initial_search_space':768,'outer_regeneration':768,'inner_iteration':256}
        if stage not in caps or type(max_tokens) is not int or not 1<=max_tokens<=caps[stage]:raise ValueError('Output-token cap exceeded')
        if not isinstance(messages,list) or not messages or any(not isinstance(x,dict) or x.get('role') not in ('system','user','assistant') or not isinstance(x.get('content'),str) for x in messages):raise ValueError('Invalid chat messages')
        if len(json.dumps(messages,ensure_ascii=False).encode())>24576:raise ValueError('Public request byte cap exceeded')
        base=self._env['PAPER_LLM_BASE_URL'].rstrip('/')
        if not base.startswith(('https://','http://')):raise ValueError('HTTP-compatible base URL required')
        endpoint=base+'/chat/completions'
        body={'model':self._env['PAPER_LLM_MODEL'],'messages':messages,'temperature':.4,'top_p':.85,'max_tokens':max_tokens}
        data=json.dumps(body,ensure_ascii=False).encode()
        headers={'Content-Type':'application/json','Authorization':'Bearer '+self._env['PAPER_LLM_API_KEY']}
        self.calls+=1
        folder=None if evidence_dir is None else Path(evidence_dir)/f'call_{self.calls:02d}'
        if folder:
            folder.mkdir(parents=True,exist_ok=False)
            (folder/'request.json').write_text(json.dumps({'stage':stage,'messages':messages,'generation':{k:v for k,v in body.items() if k!='messages'}},indent=2))
        try:
            if self._transport is None:
                request=urllib.request.Request(endpoint,data=data,headers=headers,method='POST')
                with urllib.request.urlopen(request,timeout=180) as response:
                    raw=response.read(1048577)
                if len(raw)>1048576:raise RuntimeError('API response byte cap exceeded')
                result=json.loads(raw)
            else:
                result=self._transport(endpoint,data,headers,180)
            content=result['choices'][0]['message']['content']
            if not isinstance(content,str):raise ValueError('API content must be text')
            if folder:(folder/'response.txt').write_text(content)
            value=validate(stage,parse_json(content),remaining=remaining)
            if folder:(folder/'validated.json').write_text(json.dumps(value,indent=2))
            return value
        except urllib.error.HTTPError as error:
            if folder:(folder/'error.json').write_text(json.dumps({'type':'HTTPError','status':error.code}))
            raise RuntimeError('API HTTP failure status '+str(error.code)) from None
        except (urllib.error.URLError,TimeoutError):
            if folder:(folder/'error.json').write_text('{"type":"TransportFailure"}')
            raise RuntimeError('API transport failure; endpoint/key details suppressed') from None
        except Exception as error:
            # Do not serialize exception text from an external transport.
            if folder:(folder/'error.json').write_text(json.dumps({'type':type(error).__name__,'outcome':'response_invalid_or_unavailable'}))
            raise
