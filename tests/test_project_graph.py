"""Regression tests for binding routing and truthful read-only graph rendering."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.dont_write_bytecode = True
import render_canvas as canvas
import validate_binding as binding


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.config = {'schema_version':'project-learning/binding/2',
                       'business_project_id':'case-suite','mode':'enabled',
                       'codex_project_id':'host-1','workspace_root':str(self.root),
                       'consent':'User explicitly enabled these two cases',
                       'projects':[{'project_id':'youtube','record_root':'records/youtube'},
                                   {'project_id':'self-instruct','record_root':'records/self-instruct'}]}

    def check(self, **kw):
        args = dict(project_id='host-1',target='records/youtube/experiment.md',business_project_id='youtube')
        args.update(kw)
        return binding.validate(self.config,self.root,**args)

    def test_two_projects_route_separately(self):
        self.assertTrue(self.check()['auto_archive_allowed'])
        self.assertTrue(self.check(target='records/self-instruct/run.md',business_project_id='self-instruct')['auto_archive_allowed'])

    def test_target_is_required(self):
        r=self.check(target=None)
        self.assertTrue(r['valid'])
        self.assertFalse(r['auto_archive_allowed'])
        self.assertEqual(r['scope_check'],'target_not_checked')

    def test_missing_host_cannot_enable_automatic_capture(self):
        self.assertFalse(self.check(project_id=None)['auto_archive_allowed'])

    def test_missing_business_identity(self):
        self.assertFalse(self.check(business_project_id=None)['auto_archive_allowed'])

    def test_other_business_identity(self):
        self.assertEqual(self.check(business_project_id='self-instruct')['scope_check'],'business_project_mismatch')

    def test_unrelated_target(self):
        self.assertFalse(self.check(target='skills/project-learning/README.md')['auto_archive_allowed'])

    def test_similar_prefix_not_child(self):
        self.assertFalse(self.check(target='records/youtube-other/run.md')['auto_archive_allowed'])

    def test_target_parent_escape(self):
        self.assertFalse(self.check(target='records/youtube/../../outside.md')['auto_archive_allowed'])

    def test_target_absolute_outside_workspace(self):
        self.assertFalse(self.check(target=str(self.root.parent/'outside.md'))['auto_archive_allowed'])

    def test_manual_and_paused(self):
        for mode in ['manual','paused']:
            self.config['mode']=mode
            self.assertFalse(self.check()['auto_archive_allowed'])

    def test_wrong_host(self):
        with self.assertRaises(ValueError):self.check(project_id='other-host')

    def test_wrong_workspace(self):
        with self.assertRaises(ValueError):binding.validate(self.config,self.root/'worktree')

    def test_scope_overlap(self):
        self.config['projects'][1]['record_root']='records/youtube/sub'
        with self.assertRaises(ValueError):self.check()

    def test_duplicate_business_id(self):
        self.config['projects'][1]['project_id']='youtube'
        with self.assertRaises(ValueError):self.check()

    def test_scope_cannot_escape(self):
        self.config['projects'][0]['record_root']='../outside'
        with self.assertRaises(ValueError):self.check()

    def test_no_whole_workspace_fallback(self):
        self.config['projects'][0]['record_root']='.'
        with self.assertRaises(ValueError):self.check()

    def test_consent_must_be_text(self):
        self.config['consent']=True
        with self.assertRaises(ValueError):self.check()

    def test_legacy_does_not_guess_subproject(self):
        self.config['schema_version']='project-learning/binding/1'
        self.config['record_roots']=[p['record_root'] for p in self.config.pop('projects')]
        r=self.check()
        self.assertFalse(r['auto_archive_allowed'])
        self.assertEqual(r['scope_check'],'legacy_scope_mapping_required')


class CanvasTests(unittest.TestCase):
    def setUp(self):
        self.g=json.loads((ROOT/'examples/self-instruct.json').read_text(encoding='utf-8'))

    def invalid(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):canvas.validate(self.g)

    def test_both_case_graphs(self):
        for name in ['youtube','self-instruct']:
            canvas.validate(json.loads((ROOT/'examples'/f'{name}.json').read_text(encoding='utf-8')))

    def test_no_pass_for_unexecuted_node(self):
        self.g['nodes'][1]['acceptance_status']='pass'
        self.invalid()

    def test_no_provisional_pass_for_unexecuted_node(self):
        self.g['nodes'][1]['acceptance_status']='provisional_pass'
        self.invalid()

    def test_no_tested_fail_for_unexecuted_node(self):
        self.g['nodes'][1]['acceptance_status']='fail'
        self.invalid()

    def test_pending_checks_prevent_pass(self):
        self.g['nodes'][0]['acceptance_status']='provisional_pass'
        self.invalid()

    def test_proposed_standard_not_formal_pass(self):
        n=self.g['nodes'][0];n['acceptance_status']='pass';n['pending_checks']=[]
        self.invalid()

    def test_scoped_pass_allowed(self):
        n=self.g['nodes'][0];n['acceptance_status']='pass';n['pending_checks']=[];n['criteria_authority']='agreed'
        canvas.validate(self.g)

    def test_unexecuted_runs_rejected(self):
        self.g['nodes'][1]['runs']=copy.deepcopy(self.g['nodes'][0]['runs'])
        self.invalid()

    def test_run_phase_required(self):
        del self.g['nodes'][0]['runs'][0]['phase'];self.invalid()

    def test_duplicate_run(self):
        self.g['nodes'][0]['runs']*=2;self.invalid()

    def test_replay_input_fresh_execution_visible(self):
        r=self.g['nodes'][0]['runs'][0]
        self.assertEqual((r['origin'],r['input_origin']),('fresh','replay'))
        page=canvas.render(self.g)
        self.assertIn('published_artifact_audit',page)
        self.assertIn('来源说明',page)
        self.assertIn(self.g['provenance'],page)

    def test_source_provenance_escaped(self):
        self.g['provenance']='<script>alert(1)</script>'
        page=canvas.render(self.g)
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)

    def test_duplicate_node(self):
        self.g['nodes'].append(copy.deepcopy(self.g['nodes'][0]));self.invalid()

    def test_missing_endpoint(self):
        self.g['edges'][0]['target']='missing';self.invalid()

    def test_duplicate_edge(self):
        self.g['edges'].append(copy.deepcopy(self.g['edges'][0]));self.invalid()

    def test_plan_order_cannot_claim_execution_lineage(self):
        self.g['edges'][1]['relation']='derived_from';self.invalid()

    def test_plan_order_cannot_include_completed_experiment(self):
        self.g['edges'][0]['relation']='planned_next';self.invalid()

    def test_plan_cycle(self):
        e=copy.deepcopy(self.g['edges'][1]);e['source'],e['target']=e['target'],e['source']
        self.g['edges'].append(e);self.invalid()

    def test_lineage_cycle(self):
        self.g=json.loads((ROOT/'examples/youtube.json').read_text(encoding='utf-8'))
        e=copy.deepcopy(self.g['edges'][0]);e['source'],e['target']=e['target'],e['source']
        self.g['edges'].append(e);self.invalid()

    def test_edge_basis_required(self):
        del self.g['edges'][0]['basis'];self.invalid()

    def test_plans_and_relationship_types_visible(self):
        page=canvas.render(self.g)
        for text in ['planned_stage','not_run','计划顺序','参考','新合成方案的完整业务验收']:
            self.assertIn(text,page)

    def test_legacy_graph_discloses_unknown_scope(self):
        self.g['schema_version']='project-learning/graph/1'
        for n in self.g['nodes']:del n['acceptance_scope']
        self.assertIn('旧格式未提供',canvas.render(self.g))

    def test_bad_input_controlled_cli_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'bad.json';src.write_text('[]',encoding='utf-8');dst=Path(tmp)/'index.html'
            r=subprocess.run([sys.executable,str(ROOT/'scripts/render_canvas.py'),'--graph',str(src),'--output',str(dst)],capture_output=True)
            self.assertEqual(r.returncode,2)
            self.assertFalse(dst.exists())

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'index.html';dst.write_text('original',encoding='utf-8')
            r=subprocess.run([sys.executable,str(ROOT/'scripts/render_canvas.py'),'--graph',str(ROOT/'examples/youtube.json'),'--output',str(dst)],capture_output=True)
            self.assertEqual(r.returncode,2)
            self.assertEqual(dst.read_text(encoding='utf-8'),'original')


if __name__=='__main__':unittest.main()
