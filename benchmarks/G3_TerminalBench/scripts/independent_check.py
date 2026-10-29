"""Independent semantic checks; never used as an evaluated agent input."""
import asyncio
import collections
import csv
import datetime
import importlib.util
import json
import pathlib
import re
import signal
import subprocess
import sys
import time


def check_log():
    periods = ['today', 'last_7_days', 'last_30_days', 'month_to_date', 'total']
    today = datetime.date(2025, 8, 12)
    starts = [today, today-datetime.timedelta(days=6), today-datetime.timedelta(days=29), today.replace(day=1), None]
    expected = collections.Counter()
    files = list(pathlib.Path('/app/logs').glob('*.log'))
    for f in files:
        day = datetime.date.fromisoformat(f.name[:10])
        counts = collections.Counter(re.findall(r'\[(ERROR|WARNING|INFO)\]', f.read_text()))
        for p, start in zip(periods, starts):
            if start is None or start <= day <= today:
                for sev, count in counts.items():
                    expected[p, sev] += count
    with open('/app/summary.csv', newline='') as f:
        rows = list(csv.DictReader(f))
    actual = {(r['period'], r['severity']): int(r['count']) for r in rows}
    assert len(rows) == 15 and len(actual) == 15
    assert actual == dict(expected), (actual, dict(expected))
    return {'files':len(files),'rows':len(rows),'counts_recomputed':True}


def check_regex():
    pattern = pathlib.Path('/app/regex.txt').read_text().strip()
    cases = [
        ('1.2.3.4 2025-01-01 2025-02-29', ['2025-02-29']),
        ('1.2.3.4 2025-04-31', []),
        ('01.2.3.4 2025-01-01', []),
        ('1.02.3.4 2025-01-01', []),
        ('1.2.3.04 2025-01-01', []),
        ('256.2.3.4 2025-01-01', []),
        ('1.2.3.4 abc2025-01-01', []),
        ('1.2.3.4 2025-01-01abc', []),
        ('1.2.3.4\n2025-01-01', []),
        ('2025-12-31 x 0.0.0.0', ['2025-12-31']),
    ]
    failures=[]
    for text, expected in cases:
        actual=re.findall(pattern,text,re.MULTILINE)
        if actual != expected: failures.append({'input':text,'expected':expected,'actual':actual})
    assert not failures, failures
    return {'cases':len(cases)}


CHILD = '''import asyncio,json,pathlib,sys
sys.path.insert(0,'/app')
from run import run_tasks
p=pathlib.Path('/app/events.jsonl')
def emit(t,i):
 with p.open('a') as f: f.write(json.dumps([t,i])+'\\n')
async def job(i):
 emit('start',i)
 try: await asyncio.sleep(.15 if sys.argv[1]=='normal' else 10)
 finally: emit('cleanup',i)
asyncio.run(run_tasks([lambda i=i: job(i) for i in range(5)],2))
'''


def check_async():
    records=[]
    for mode in ['normal','cancel']:
        p=pathlib.Path('/app/events.jsonl'); p.unlink(missing_ok=True)
        proc=subprocess.Popen([sys.executable,'-c',CHILD,mode],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if mode=='cancel':
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                if p.exists() and len(p.read_text().splitlines())>=2: break
                time.sleep(.01)
            proc.send_signal(signal.SIGINT)
        try: _,err=proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill();proc.communicate();raise
        events=[json.loads(x) for x in p.read_text().splitlines()]
        active=set(); starts=[]; cleans=[]; peak=0
        for kind,i in events:
            if kind=='start': active.add(i);starts.append(i);peak=max(peak,len(active))
            else: active.remove(i);cleans.append(i)
        assert not active and sorted(starts)==sorted(cleans)
        assert peak==2
        assert len(starts)==(5 if mode=='normal' else 2),events
        records.append({'mode':mode,'started':len(starts),'cleaned':len(cleans),'peak':peak,'exit':proc.returncode,'events':events})
    return {'records':records,'evidence':'filesystem events, no stdout matching'}


if __name__=='__main__':
    try:
        detail={'log-summary-date-ranges':check_log,'regex-log':check_regex,'cancel-async-tasks':check_async}[sys.argv[1]]()
        print(json.dumps({'passed':True,'detail':detail}))
    except Exception as exc:
        print(json.dumps({'passed':False,'error':repr(exc)}))
        sys.exit(1)
