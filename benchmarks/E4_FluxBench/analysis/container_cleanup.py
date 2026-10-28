"""Stop only an exact named container whose E4 mount and script are verified."""
import json,subprocess

def stop_owned_container(name,out,script):
    probe=subprocess.run(['podman','inspect',name],capture_output=True,text=True,timeout=15)
    if probe.returncode:
        return dict(name=name,already_absent=True,inspect_returncode=probe.returncode)
    data=json.loads(probe.stdout)[0]
    assert any(m.get('Source')==str(out) and m.get('Destination')=='/out' for m in data['Mounts'])
    assert script in data['Config']['Cmd']
    p=subprocess.run(['podman','stop','--time','1',name],capture_output=True,text=True,timeout=15)
    assert p.returncode==0,p.stderr
    return dict(name=name,verified_owned_mount=True,script=script,returncode=p.returncode)
