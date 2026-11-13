"""Check a binding and proposed record target; never writes business records."""
import argparse
import json
import sys
from pathlib import Path


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected nonempty text: '+name)
    return value


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate(d, workspace, project_id=None, target=None, business_project_id=None):
    if not isinstance(d, dict) or d.get('schema_version') not in {'project-learning/binding/1','project-learning/binding/2'}:
        raise ValueError('Invalid binding schema')
    for name in ('business_project_id','consent','codex_project_id','workspace_root','mode'):
        text(d.get(name), name)
    if d['mode'] not in {'enabled','manual','paused'}:
        raise ValueError('Invalid mode')
    if not Path(d['workspace_root']).is_absolute():
        raise ValueError('workspace_root must be absolute')
    root=Path(d['workspace_root']).resolve()
    if root!=Path(workspace).resolve():
        raise ValueError('Workspace mismatch; register migration/worktree explicitly')
    if project_id is not None and d.get('codex_project_id')!=project_id:
        raise ValueError('Codex project identity mismatch')
    legacy = d['schema_version'].endswith('/1')
    entries = d.get('record_roots') if legacy else d.get('projects')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Missing project scopes')
    scopes, ids = [], set()
    for entry in entries:
        if legacy:
            pid, item = None, entry
        else:
            if not isinstance(entry, dict):
                raise ValueError('Project scope must be an object')
            pid, item = text(entry.get('project_id'), 'project_id'), entry.get('record_root')
            if pid in ids:
                raise ValueError('Duplicate business project')
            ids.add(pid)
        path = Path(text(item, 'record_root'))
        if path.is_absolute() or path.drive or '..' in path.parts or str(path)=='.':
            raise ValueError('Use a specific relative record directory')
        resolved = (root/path).resolve()
        if not inside(resolved, root):
            raise ValueError('Record root escapes workspace')
        if any(inside(resolved, other) or inside(other, resolved) for _, other in scopes):
            raise ValueError('Overlapping record scopes are ambiguous')
        scopes.append((pid,resolved))
    reason, matched = 'target_not_checked', None
    if target is not None:
        proposed = Path(text(str(target), 'target'))
        proposed = (proposed if proposed.is_absolute() else root/proposed).resolve()
        matches = [pid for pid,path in scopes if inside(proposed,path)]
        if not matches:
            reason = 'target_out_of_scope'
        elif legacy:
            reason = 'legacy_scope_mapping_required'
        else:
            matched = matches[0]
            reason = ('business_project_not_checked' if business_project_id is None else
                      'business_project_mismatch' if business_project_id != matched else 'matched')
    return {'valid':True,'mode':d['mode'],
            'host_identity':'confirmed' if project_id is not None else 'not_checked',
            'scope_check':reason,'matched_project_id':matched,
            'auto_archive_allowed':reason=='matched' and project_id is not None and d['mode']=='enabled',
            'background_capture':False,
            'limitation':'Checks supplied identity and target, not conversational relevance or authority of consent text.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--workspace',required=True)
    p.add_argument('--codex-project-id')
    p.add_argument('--target', help='Proposed record path, absolute or relative to workspace')
    p.add_argument('--business-project-id', help='Business project selected for this record')
    a=p.parse_args()
    try:
        report=validate(json.loads(a.binding.read_text(encoding='utf-8-sig')),a.workspace,a.codex_project_id,a.target,a.business_project_id)
        print(json.dumps(report,ensure_ascii=False))
        raise SystemExit(0 if report['auto_archive_allowed'] else 1)
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('Binding error:',e,file=sys.stderr)
        raise SystemExit(2)
