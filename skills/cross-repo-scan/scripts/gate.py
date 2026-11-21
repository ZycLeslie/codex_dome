#!/usr/bin/env python3
"""Conservative review-result evaluator; not a release attestation service."""
import json
import sys

CODES = {'PASS': 0, 'BLOCK': 2, 'REVIEW': 3, 'INCOMPLETE': 4}

def evaluate(d):
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    require(type(d) is dict and d.get('schema_version') == 1, 'unsupported schema')
    require(d.get('mode') in ('full','daily-mr','mr-review'), 'invalid mode')
    require(isinstance(d.get('snapshot_id'), str) and bool(d['snapshot_id']), 'missing snapshot')
    for flag in ('scope_complete','evidence_checked','release_context_complete','empty_scope_verified'):
        require(type(d.get(flag)) is bool, 'missing boolean '+flag)
    require(type(d.get('tasks')) is list and type(d.get('findings')) is list and type(d.get('errors')) is list, 'missing arrays')
    seen=set()
    unfinished=False
    for t in d['tasks']:
        require(type(t) is dict and isinstance(t.get('id'),str) and t['id'] and t['id'] not in seen, 'invalid task id')
        seen.add(t['id'])
        require(t.get('status') in ('completed','unknown','failed','pending'), 'invalid task status')
        unfinished |= t['status'] != 'completed'
    require(bool(seen) or d['empty_scope_verified'], 'empty task plan unverified')
    block=[]
    review=[]
    ids=set()
    for f in d['findings']:
        require(type(f) is dict and isinstance(f.get('id'),str) and f['id'] and f['id'] not in ids, 'invalid finding id')
        ids.add(f['id'])
        require(f.get('task_id') in seen, 'finding references unknown task')
        require(f.get('severity') in ('critical','high','medium','low'), 'invalid severity')
        require(f.get('status') in ('confirmed','suspected','disproved'), 'invalid finding status')
        require(f.get('evidence_level') in ('reproduced','static','hypothesis'), 'invalid evidence level')
        require(type(f.get('active')) is bool and type(f.get('reviewed')) is bool, 'missing finding flags')
        require(type(f.get('evidence')) is list, 'missing evidence')
        if f['status']=='confirmed':
            require(f['evidence_level']!='hypothesis' and f['reviewed'] and bool(f['evidence']), 'unsupported confirmation')
        if not f['active'] or f['status']=='disproved':
            require(bool(f.get('resolution_evidence')), 'missing resolution evidence')
            continue
        if f['severity'] in ('critical','high'):
            if f['status']=='confirmed': block.append(f['id'])
            else: review.append(f['id'])
    complete = (d['scope_complete'] and d['evidence_checked'] and d['release_context_complete'] and not d['errors'] and not unfinished)
    status = 'BLOCK' if block else 'INCOMPLETE' if not complete else 'REVIEW' if review else 'PASS'
    return {'schema_version':1,'snapshot_id':d['snapshot_id'],'status':status,'coverage_complete':complete,'blocking_findings':block,'review_findings':review,'authority':'advisory-until-host-verified'}

def main():
    try:
        if len(sys.argv)!=2: raise ValueError('usage: gate.py review.json')
        with open(sys.argv[1], encoding='utf-8') as f: result=evaluate(json.load(f))
    except (ValueError, OSError, TypeError, KeyError) as e:
        result={'status':'INCOMPLETE','error':str(e),'authority':'advisory-until-host-verified'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return CODES[result['status']]

if __name__=='__main__': sys.exit(main())
