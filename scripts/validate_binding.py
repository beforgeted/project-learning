"""Check a binding against explicit host context; never enables capture itself."""
import argparse
import json
from pathlib import Path


def validate(d, workspace, project_id=None):
    if d.get('schema_version')!='project-learning/binding/1':
        raise ValueError('Invalid binding schema')
    if not d.get('business_project_id') or not d.get('consent'):
        raise ValueError('Missing identity or consent')
    if d.get('mode') not in {'enabled','manual','paused'}:
        raise ValueError('Invalid mode')
    root=Path(d['workspace_root']).resolve()
    if root!=Path(workspace).resolve():
        raise ValueError('Workspace mismatch; register migration/worktree explicitly')
    if project_id is not None and d.get('codex_project_id')!=project_id:
        raise ValueError('Codex project identity mismatch')
    if not isinstance(d.get('record_roots'),list) or not d['record_roots']:
        raise ValueError('Missing record roots')
    for item in d['record_roots']:
        path=Path(item)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Record root must remain inside workspace')
        (root/path).resolve().relative_to(root)
    return {'valid':True,'mode':d['mode'],'host_identity':'confirmed' if project_id is not None else 'not_checked','background_capture':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--workspace',required=True)
    p.add_argument('--codex-project-id')
    a=p.parse_args()
    try:
        print(json.dumps(validate(json.loads(a.binding.read_text(encoding='utf-8-sig')),a.workspace,a.codex_project_id)))
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('Binding error:',e)
        raise SystemExit(2)
