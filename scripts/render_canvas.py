"""Validate an experiment graph and render an offline, read-only HTML view."""
import argparse
import html
import json
import sys
import textwrap
from pathlib import Path


def require_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected nonempty text: '+name)
    return value


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') not in {'project-learning/graph/1','project-learning/graph/2'}:
        raise ValueError('Unsupported graph schema')
    version2 = data['schema_version'].endswith('/2')
    if not isinstance(data.get('project_id'), str) or not data['project_id']:
        raise ValueError('Missing project_id')
    nodes, edges = data['nodes'], data['edges']
    if not isinstance(nodes, list) or not nodes or not isinstance(edges, list):
        raise ValueError('Expected nonempty nodes list and edges list')
    if version2:
        require_text(data.get('provenance'), 'provenance')
    ids = set()
    for n in nodes:
        if not isinstance(n, dict):
            raise ValueError('Node must be an object')
        for key in ('id', 'title', 'question', 'change'):
            if not isinstance(n.get(key), str) or not n[key]:
                raise ValueError('Missing node field: ' + key)
        if n['id'] in ids:
            raise ValueError('Duplicate node ID')
        ids.add(n['id'])
        if n['execution_status'] not in {'planned','running','completed','failed','aborted','not_run'}:
            raise ValueError('Invalid execution status')
        if n['acceptance_status'] not in {'pass','fail','incomplete','unknown','provisional_pass','not_assessed'}:
            raise ValueError('Invalid acceptance status')
        if n['execution_status'] != 'completed' and n['acceptance_status'] in {'pass','provisional_pass'}:
            raise ValueError('Uncompleted execution cannot claim acceptance pass')
        if n['execution_status'] in {'planned','not_run'} and n['acceptance_status']=='fail':
            raise ValueError('Unexecuted node cannot claim tested failure')
        if version2:
            if n.get('kind') not in {'experiment','planned_stage'}:
                raise ValueError('Invalid node kind')
            if n['kind']=='planned_stage' and n['execution_status'] not in {'planned','not_run'}:
                raise ValueError('A planned stage is not an executed experiment')
            require_text(n.get('acceptance_scope'), 'acceptance_scope')
            if n.get('criteria_authority') not in {'agreed','proposed','unknown'}:
                raise ValueError('Invalid criteria authority')
            if not isinstance(n.get('pending_checks'),list):
                raise ValueError('pending_checks must be a list')
            for check in n['pending_checks']:
                require_text(check, 'pending check')
            if n['acceptance_status'] in {'pass','provisional_pass'} and n['pending_checks']:
                raise ValueError('Acceptance cannot pass with required checks pending')
            if n['acceptance_status']=='pass' and n['criteria_authority']!='agreed':
                raise ValueError('Formal pass requires agreed criteria')
        if not isinstance(n['evidence'], list) or not isinstance(n['runs'], list):
            raise ValueError('Evidence and runs must be lists')
        for e in n['evidence']:
            if not isinstance(e,dict):
                raise ValueError('Evidence must be an object')
            if not isinstance(e.get('locator'), str) or not e['locator']:
                raise ValueError('Missing evidence locator')
        if version2 and not n['evidence']:
            raise ValueError('Missing source evidence or plan reference')
        if n['execution_status'] in {'planned','not_run'} and n['runs']:
            raise ValueError('Unexecuted node cannot claim runs')
        for r in n['runs']:
            if not isinstance(r,dict):
                raise ValueError('Run must be an object')
            if not r.get('run_id') or not r.get('attempt_id') or r.get('origin') not in {'fresh','cache','replay','unknown'}:
                raise ValueError('Invalid run')
            require_text(r['run_id'],'run_id')
            require_text(r['attempt_id'],'attempt_id')
            if version2:
                require_text(r.get('phase'), 'run phase')
                if r.get('input_origin') not in {'fresh','cache','replay','unknown'}:
                    raise ValueError('Invalid input origin')
        if len({(r['run_id'],r['attempt_id']) for r in n['runs']}) != len(n['runs']):
            raise ValueError('Duplicate run attempt')
    adjacency = {i: [] for i in ids}
    by_id = {n['id']:n for n in nodes}
    seen_edges = set()
    for e in edges:
        if not isinstance(e,dict):
            raise ValueError('Edge must be an object')
        if e['source'] not in ids or e['target'] not in ids or e['source'] == e['target']:
            raise ValueError('Invalid edge endpoint')
        if e['relation'] not in {'derived_from','retests','combines','compares','references','planned_next'}:
            raise ValueError('Invalid relation')
        key=(e['source'],e['target'],e['relation'])
        if key in seen_edges:
            raise ValueError('Duplicate edge')
        seen_edges.add(key)
        if version2:
            require_text(e.get('basis'),'edge basis')
            if e['relation']=='planned_next' and any(by_id[i]['kind']!='planned_stage' for i in (e['source'],e['target'])):
                raise ValueError('planned_next requires planned stages')
            if e['relation'] in {'derived_from','retests','combines'} and any(by_id[i]['kind']!='experiment' for i in (e['source'],e['target'])):
                raise ValueError('Experiment lineage cannot connect generic planned stages')
        if e['relation'] in {'derived_from','retests','combines','planned_next'}:
            adjacency[e['source']].append(e['target'])
    visiting, done = set(), set()
    def visit(i):
        if i in visiting:
            raise ValueError('Cyclic experiment lineage')
        if i in done:
            return
        visiting.add(i)
        for j in adjacency[i]:
            visit(j)
        visiting.remove(i)
        done.add(i)
    for i in ids:
        visit(i)
    return nodes, edges


def render(data):
    nodes, edges = validate(data)
    esc = lambda x: html.escape(str(x), quote=True)
    coords = {n['id']: (40, 30+i*150) for i,n in enumerate(nodes)}
    height = len(nodes)*150+30
    names={'derived_from':'派生','retests':'复验','combines':'组合','compares':'对照','references':'参考','planned_next':'计划顺序'}
    svg = [f'<svg viewBox="0 0 920 {height}" role="img" aria-label="实验关系图，详细状态与关系见下方列表">',
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#718096"/></marker></defs>']
    for j,e in enumerate(edges):
        x,y = coords[e['source']]; a,b = coords[e['target']]
        rail=690+(j%6)*30
        dash=' stroke-dasharray="6 5"' if e['relation'] in {'references','planned_next'} else ''
        arrow='' if e['relation']=='compares' else ' marker-end="url(#arrow)"'
        svg.append(f'<path d="M640,{y+55} H{rail} V{b+55} H640" fill="none" stroke="#718096" stroke-width="2"{dash}{arrow}/><text x="{rail+5}" y="{(y+b)//2+55}" font-size="12">{esc(names[e["relation"]])}</text>')
    details=[]
    for i,n in enumerate(nodes):
        x,y=coords[n['id']]
        color='#fff4d5' if n['execution_status'] in {'planned','not_run'} else '#e8f1fb'
        lines=textwrap.wrap(n['title'],width=27)[:2]
        title=''.join(f'<tspan x="{x+15}" dy="{0 if k==0 else 23}">{esc(line)}</tspan>' for k,line in enumerate(lines))
        svg.append(f'<a href="#node-{i}"><title>{esc(n["title"])}</title><rect x="{x}" y="{y}" width="600" height="115" rx="12" fill="{color}" stroke="#94a3b8"/><text x="{x+15}" y="{y+27}">{title}</text><text x="{x+15}" y="{y+90}" font-size="14">执行 {esc(n["execution_status"])} · 验收 {esc(n["acceptance_status"])}</text></a>')
        pending='；'.join(n.get('pending_checks',[])) or ('无已声明待办' if 'pending_checks' in n else '旧格式未提供，不能推断完成')
        details.append(f'<section id="node-{i}"><small>{esc(n.get("kind","legacy_kind_unknown"))} · {esc(n["id"])}</small><h2>{esc(n["title"])}</h2><p>执行：<b>{esc(n["execution_status"])}</b> ｜ 验收：<b>{esc(n["acceptance_status"])}</b></p><p>验收范围：{esc(n.get("acceptance_scope","旧格式未提供"))}</p><p>标准来源：{esc(n.get("criteria_authority","unknown"))} · 待完成：{esc(pending)}</p><details><summary>记录、运行来源与证据</summary><pre>{esc(json.dumps(n,ensure_ascii=False,indent=2))}</pre></details></section>')
    svg.append('</svg>')
    edge_rows=''.join(f'<li>{esc(e["source"])} {"↔" if e["relation"]=="compares" else "→"} {esc(e["target"])}：{esc(names[e["relation"]])}<br>{esc(e.get("basis","旧格式无关系依据"))}</li>' for e in edges)
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>实验画布</title><style>body{font:16px system-ui,sans-serif;background:#f4f7fb;color:#172b4d;max-width:1100px;margin:32px auto;padding:20px}svg{width:100%;background:white;border-radius:16px}section{background:white;padding:24px;margin:20px 0;border-radius:12px}pre,li{overflow-wrap:anywhere}pre{white-space:pre-wrap;font:14px monospace}li{margin:12px}summary{cursor:pointer}.notice{border-left:4px solid #b7791f;padding:14px;background:#fff4d5}</style><h1>'+esc(data['project_id'])+'</h1><p>只读证据视图 · 黄色表示计划或未执行 · 虚线表示参考或计划关系；所有连线均不启动实验。</p><div class="notice">来源说明：'+esc(data.get('provenance','旧格式未提供来源说明'))+'<br>仅展示提供的记录；原文件及其哈希未由画布生成器独立核验。</div>'+''.join(svg)+'<h2>关系及依据</h2><ul>'+edge_rows+'</ul>'+''.join(details)+'</html>'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        result=render(json.loads(a.graph.read_text(encoding='utf-8-sig')))
        with a.output.open('x',encoding='utf-8') as f:
            f.write(result)
        print(a.output.resolve())
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as e:
        print('Canvas error:',e,file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
