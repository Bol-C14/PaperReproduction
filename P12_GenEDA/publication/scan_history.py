"""Scan every object reachable from one proposed publication branch.

Only rule names, paths, offsets and hostname summaries are emitted, never values.
"""
import argparse
import collections
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import urllib.parse

import secret_patterns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--branch', default='refs/heads/reproduction/geneda-iccad2025')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    def git(*words):
        return subprocess.check_output(['git', '-C', args.repo, *words])
    counts, findings, hosts, url_flags = collections.Counter(), [], collections.Counter(), []
    objects = git('rev-list', '--objects', args.branch).decode().splitlines()
    for entry in objects:
        oid, _, name = entry.partition(' ')
        kind = git('cat-file', '-t', oid).decode().strip()
        if kind not in ['blob', 'commit', 'tag']:
            continue
        raw = git('cat-file', kind, oid)
        counts[kind] += 1
        findings += secret_patterns.scan(raw, 'git:' + oid + (':' + name if name else ''))
        for match in re.finditer(rb'https?://[^\s\x00\"\'<>]+', raw):
            try:
                u = urllib.parse.urlsplit(match.group().decode('utf-8', 'ignore'))
                host = u.hostname
            except ValueError:
                continue
            if not host:
                continue
            hosts[host] += 1
            try:
                private = not ipaddress.ip_address(host).is_global
            except ValueError:
                private = host.endswith(('.internal', '.local', '.openai.org'))
            if private or u.username or u.password or re.search(r'(token|signature|credential|api_key|auth)=', u.query, re.I):
                url_flags.append({'object': oid, 'path': name, 'hostname': host})
    report = {'branch': args.branch, 'head': git('rev-parse', args.branch).decode().strip(),
              'object_counts': dict(counts), 'potential_secret_findings': findings,
              'hostname_counts': dict(hosts), 'url_manual_review_flags': url_flags,
              'values_printed': False,
              'coverage': 'All reachable blob/commit/tag objects, including deleted versions; gzip/ZIP/NPZ expansion; URL credential/private-host review. Heuristic pattern inspection, not a universal secret certification.'}
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'head': report['head'], 'object_counts': report['object_counts'],
                      'potential_secret_findings': len(findings), 'url_review_flags': len(url_flags)}))
    raise SystemExit(bool(findings or url_flags))


if __name__ == '__main__':
    main()
