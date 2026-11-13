"""Validate an experiment graph and render an offline, read-only HTML view."""
import argparse
import html
import json
from pathlib import Path


def validate(data):
    if data.get('schema_version') != 'project-learning/graph/1':
        raise ValueError('Unsupported graph schema')
    if not isinstance(data.get('project_id'), str) or not data['project_id']:
        raise ValueError('Missing project_id')
    nodes, edges = data['nodes'], data['edges']
    ids = set()
    for n in nodes:
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
        if not isinstance(n['evidence'], list) or not isinstance(n['runs'], list):
            raise ValueError('Evidence and runs must be lists')
        for e in n['evidence']:
            if not isinstance(e.get('locator'), str) or not e['locator']:
                raise ValueError('Missing evidence locator')
        if n['execution_status'] in {'planned','not_run'} and n['runs']:
            raise ValueError('Unexecuted node cannot claim runs')
        for r in n['runs']:
            if not r.get('run_id') or not r.get('attempt_id') or r.get('origin') not in {'fresh','cache','replay','unknown'}:
                raise ValueError('Invalid run')
    adjacency = {i: [] for i in ids}
    for e in edges:
        if e['source'] not in ids or e['target'] not in ids or e['source'] == e['target']:
            raise ValueError('Invalid edge endpoint')
        if e['relation'] not in {'derived_from','retests','combines','compares','references'}:
            raise ValueError('Invalid relation')
        if e['relation'] in {'derived_from','retests','combines'}:
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
    coords = {n['id']: (40 + (i % 2)*510, 40+(i//2)*180) for i,n in enumerate(nodes)}
    height = max(220, ((len(nodes)+1)//2)*180+40)
    svg = [f'<svg viewBox="0 0 1040 {height}" role="img" aria-label="实验关系图">',
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#718096"/></marker></defs>']
    for e in edges:
        x,y = coords[e['source']]; a,b = coords[e['target']]
        svg.append(f'<line x1="{x+210}" y1="{y+100}" x2="{a+210}" y2="{b}" stroke="#718096" stroke-width="2" marker-end="url(#arrow)"/>')
    details=[]
    for i,n in enumerate(nodes):
        x,y=coords[n['id']]
        color='#fff4d5' if n['execution_status'] in {'planned','not_run'} else '#e8f1fb'
        svg.append(f'<a href="#node-{i}"><rect x="{x}" y="{y}" width="420" height="100" rx="12" fill="{color}" stroke="#94a3b8"/><text x="{x+15}" y="{y+30}">{esc(n["title"][:28])}</text><text x="{x+15}" y="{y+65}" font-size="13">{esc(n["execution_status"])} · 验收 {esc(n["acceptance_status"])}</text></a>')
        details.append(f'<section id="node-{i}"><h2>{esc(n["title"])}</h2><pre>{esc(json.dumps(n,ensure_ascii=False,indent=2))}</pre></section>')
    svg.append('</svg>')
    edge_rows=''.join(f'<li>{esc(e["source"])} → {esc(e["target"])}：{esc(e["relation"])}</li>' for e in edges)
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>实验画布</title><style>body{font:16px system-ui,sans-serif;background:#f4f7fb;color:#172b4d;max-width:1100px;margin:32px auto;padding:20px}svg{width:100%;background:white;border-radius:16px}section{background:white;padding:24px;margin:20px 0;border-radius:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px monospace}li{margin:8px}</style><h1>'+esc(data['project_id'])+'</h1><p>只读证据视图 · 黄色表示计划或未执行 · 点击节点查看详情。连线不表示自动执行；关系类型见下表。</p>'+''.join(svg)+'<h2>关系</h2><ul>'+edge_rows+'</ul>'+''.join(details)+'</html>'


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
        print('Canvas error:',e)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
