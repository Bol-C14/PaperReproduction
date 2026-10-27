"""Offline protocol translation for a future local NeMo Responses facade.
Remote traffic, if later authorized, MUST be /chat/completions only.
Does not start a server or claim full NeMo/Pydantic runtime integration.
"""
import json
from chat_adapter import MODEL,Stopped,build_request,parse_response

def _text(content):
    if isinstance(content,str):return content
    if isinstance(content,list):
        parts=[]
        for part in content:
            if part.get('type') not in ('input_text','output_text') or not isinstance(part.get('text'),str):raise Stopped('non-text Responses content unsupported')
            parts.append(part['text'])
        return '\n'.join(parts)
    raise Stopped('unknown text content')

def responses_to_chat(body):
    allowed={'input','tools','temperature','max_output_tokens','model','parallel_tool_calls','instructions','stream','metadata'}
    if set(body)-allowed:raise Stopped('unsupported Responses fields; no silent loss')
    if body.get('stream'):raise Stopped('streaming disabled')
    items=body.get('input');messages=[];pending=set()
    if body.get('instructions'):messages.append({'role':'system','content':_text(body['instructions'])})
    if isinstance(items,str):items=[{'role':'user','content':items}]
    if not isinstance(items,list):raise Stopped('input required')
    for x in items:
        kind=x.get('type','message')
        if kind=='message':
            if pending:raise Stopped('unresolved tool calls before message')
            role=x.get('role')
            if role=='developer':role='system' # Explicit privilege mapping, covered by tests.
            messages.append({'role':role,'content':_text(x.get('content'))})
        elif kind=='function_call':
            if pending:raise Stopped('multiple pending calls unsupported')
            cid=x.get('call_id')
            if not cid or not x.get('name') or not isinstance(x.get('arguments'),str):raise Stopped('invalid function call')
            messages.append({'role':'assistant','content':None,'tool_calls':[{'id':cid,'type':'function','function':{'name':x['name'],'arguments':x['arguments']}}]});pending.add(cid)
        elif kind=='function_call_output':
            if x.get('call_id') not in pending:raise Stopped('orphan/mismatched tool result')
            if not isinstance(x.get('output'),str):raise Stopped('tool output must be text')
            messages.append({'role':'tool','tool_call_id':x['call_id'],'content':x['output']});pending.remove(x['call_id'])
        else:raise Stopped('unsupported Responses item; reasoning is not silently replayed')
    if pending:raise Stopped('unresolved tool result')
    tools=[]
    for t in body.get('tools',[]):
        if t.get('type')!='function' or not t.get('name'):raise Stopped('unsupported Responses tool')
        # Strict subset; provider-specific fields must be reviewed rather than dropped.
        if set(t)-{'type','name','description','parameters','strict'}:raise Stopped('unknown tool fields')
        f={k:v for k,v in t.items() if k not in {'type','strict'}}
        tools.append({'type':'function','function':f})
    return build_request(messages,tools=tools,max_tokens=body.get('max_output_tokens',512),temperature=body.get('temperature',.2))

def chat_to_responses(body,allowed_tools):
    p=parse_response(body,allowed_tools);out=[]
    if p['content']:out.append({'type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':p['content'],'annotations':[]}]})
    for c in p['tool_calls']:out.append({'type':'function_call','call_id':c['id'],'name':c['name'],'arguments':json.dumps(c['arguments'],separators=(',',':')),'status':'completed'})
    return {'object':'response','model':MODEL,'status':'incomplete' if p['finish_reason']=='length' else 'completed','output':out,'parallel_tool_calls':False,'usage':{'input_tokens':p['usage']['prompt_tokens'],'output_tokens':p['usage']['completion_tokens'],'total_tokens':p['usage']['total_tokens']}}
