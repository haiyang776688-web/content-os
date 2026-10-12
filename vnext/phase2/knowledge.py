"""Writing skills, source provenance and conservative script integrity checks."""
from __future__ import annotations

import json
import re
from pathlib import Path

from vnext.contracts import utc_now
from vnext.phase2.contracts import (BoundScript, EditorialVoiceProfile, EffectiveSkillSnapshot,
    FactPack, HookRuleSet, RetentionRuleSet, RuleSet, SkillLayer, Source, WritingRule)
from vnext.storage.store import Store, canonical, digest

LAYERS = ['CONSTITUTION','SYSTEM','ROLE','PROJECT','CHARACTER_STYLE','RUN']
HARD_RULES = [WritingRule(rule_id='NO_FABRICATION', name='Claim discipline', scope='SCRIPT',
    hard_or_soft='HARD', severity='BLOCKER', applies_to=['SCRIPT_PRIMARY','SCRIPT_EDITOR','AUDIT'],
    text='Never fabricate facts, sources or numbers. Preserve source-bound claims.'),
    WritingRule(rule_id='OWNER_ONLY', name='Single writer', scope='ALL', hard_or_soft='HARD',
    severity='BLOCKER', text='Downstream submits a change request; never edits upstream.'),
    WritingRule(rule_id='CREATIVE_POLICY', name='Creative policy', scope='ALL', hard_or_soft='HARD',
    severity='BLOCKER', text='Human creative policy outranks optimization metrics.')]
DEFAULT_RULES = RuleSet(set_id='WRITING_V1', rules=[
    *HARD_RULES, WritingRule(rule_id='ORAL_CLARITY',name='Spoken clarity',scope='SCRIPT',
        text='Use concise spoken clauses; explain jargon; remove empty repetition.')])


class Knowledge:
    def __init__(self, store: Store):
        self.store = store

    def require(self, pid: str, artifact_id: str, kind: str | None = None):
        item = self.store.get_artifact(artifact_id)
        if item['project_id'] != pid:
            raise ValueError('CROSS_PROJECT_ARTIFACT')
        if kind and item['artifact_type'] != kind:
            raise ValueError('WRONG_ARTIFACT_TYPE')
        if not self.store.is_usable_input(artifact_id) or item['current_status'] in ('FAILED','BLOCKED'):
            raise ValueError('STALE_OR_BLOCKED_INPUT')
        return item

    def initialize(self, pid: str):
        project = self.store.get_project(pid)
        project.phase2_enabled = True
        self.store.save_project(project)
        from vnext.phase2.configuration import visual_config
        visual_config(self.store,pid)
        values = {'WRITING_RULE_SET': DEFAULT_RULES.model_dump(),
                  'HOOK_RULE_SET': HookRuleSet(hook_type='DIRECT_VALUE').model_dump(),
                  'RETENTION_RULE_SET': RetentionRuleSet().model_dump(),
                  'EDITORIAL_VOICE': EditorialVoiceProfile(profile_id='COMPANION_V1').model_dump()}
        for kind, payload in values.items():
            if not self.store.latest(pid, kind):
                self.rules(pid, kind, payload, 'EVOLUTION')
        return values

    def rules(self, pid: str, kind: str, payload: dict, actor: str):
        if actor != 'EVOLUTION':
            raise PermissionError('EVOLUTION_ONLY_FORMAL_RULES')
        models = {'WRITING_RULE_SET': RuleSet, 'HOOK_RULE_SET': HookRuleSet,
                  'RETENTION_RULE_SET': RetentionRuleSet, 'EDITORIAL_VOICE': EditorialVoiceProfile}
        if kind not in models:
            raise ValueError('UNKNOWN_RULE_SET')
        checked = models[kind].model_validate(payload).model_dump()
        from vnext.core.governance import Governance
        return Governance(self.store).save_rule_set(pid,kind,checked,actor)

    def snapshot(self, pid: str, role: str, run_layers: list[dict] | None = None):
        system = self.store.latest(pid, 'WRITING_RULE_SET')
        layers = [SkillLayer(skill_id='CONSTITUTION_V1', layer='CONSTITUTION', rules=HARD_RULES),
                  SkillLayer(skill_id='WRITING_V1', layer='SYSTEM',
                    version=str(system['revision']) if system else '1',
                    rules=RuleSet.model_validate(system['payload']).rules if system else DEFAULT_RULES.rules)]
        layers += [SkillLayer.model_validate(x) for x in (run_layers or [])]
        if any(x.layer in ('CONSTITUTION','SYSTEM') for x in layers[2:]):
            raise PermissionError('RESERVED_SKILL_LAYER')
        effective, overrides = {}, []
        for layer in sorted(layers, key=lambda x: LAYERS.index(x.layer)):
            for rule in layer.rules:
                old = effective.get(rule.rule_id)
                if old and old.hard_or_soft == 'HARD' and old.model_dump() != rule.model_dump():
                    raise PermissionError('HARD_RULE_OVERRIDE:'+rule.rule_id)
                if old and old.model_dump() != rule.model_dump():
                    overrides.append({'rule_id': rule.rule_id, 'layer': layer.layer})
                effective[rule.rule_id] = rule
        value = EffectiveSkillSnapshot(role=role, skill_versions=[
            {'skill_id':x.skill_id,'version':x.version,'layer':x.layer} for x in layers],
            resolution_order=LAYERS, rules=list(effective.values()), overrides=overrides).model_dump()
        # One snapshot stream per role avoids staling the script when Audit resolves its skills.
        kind = 'EFFECTIVE_SKILL_SNAPSHOT_'+role
        dependencies = [self.store.dependency(system['artifact_id'])] if system else []
        for name in ('HOOK_RULE_SET','RETENTION_RULE_SET','EDITORIAL_VOICE','RULE_CATALOG'):
            item = self.store.latest(pid, name)
            if item:
                dependencies.append(self.store.dependency(item['artifact_id']))
                value['rule' if name=='RULE_CATALOG' else name.lower()] = item['payload']
        existing = self.store.latest(pid, kind)
        if existing and existing['output_hash'] == digest(value) and self.store.is_usable_input(existing['artifact_id']):
            return existing
        return self.store.create_artifact(pid, kind, value, role='SKILL_RESOLVER', dependencies=dependencies).model_dump()

    def source(self, pid: str, payload: dict, actor='RESEARCH'):
        if actor != 'RESEARCH':
            raise PermissionError('RESEARCH_ONLY_SOURCE')
        value = Source.model_validate(payload)
        result = self.store.create_artifact(pid, 'SOURCE_'+value.source_id, value.model_dump(), role=actor)
        path = self.store.root/'projects'/pid/'research'/'source_ledger.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.store.lock, path.open('ab') as file:
            file.write(canonical({'artifact_id':result.artifact_id,'revision':result.revision, **value.model_dump()})+b'\n')
        return result.model_dump()

    def disagreement(self,pid,target_id,opinions):
        if len(opinions)<2: raise ValueError('DISAGREEMENT_REQUIRES_TWO_OPINIONS')
        self.require_no_disagreement(pid)
        target=self.require(pid,target_id)
        routed=target
        if target['artifact_type']=='SCRIPT':
            routed=self.store.latest(pid,'FACT_PACK') or target
        result=self.store.create_artifact(pid,'DISAGREEMENT',{'target_artifact_id':target_id,
            'owner':'RESEARCH' if target['artifact_type'] in ('SCRIPT','FACT_PACK') else target['created_by_role'],
            'opinions':opinions,'resolution':'PENDING','automatic_vote':False},role='AUDIT',
            dependencies=[self.store.dependency(target_id)])
        project=self.store.get_project(pid);project.state='DISAGREEMENT';self.store.save_project(project)
        from vnext.core.runtime import Runtime
        Runtime(self.store).change_request(pid,routed['artifact_id'],'AUDIT','Model disagreement: resolve using evidence, no majority vote')
        return result.model_dump()

    def resolve_disagreement(self,pid,disagreement_id,evidence_ids,reason,actor):
        # Repairing the disputed input intentionally stales the original finding.
        # Resolution cites the historical finding but depends on the current evidence.
        disagreement=self.store.get_artifact(disagreement_id)
        latest=self.store.latest(pid,'DISAGREEMENT')
        if disagreement['project_id']!=pid or disagreement['artifact_type']!='DISAGREEMENT' or latest['artifact_id']!=disagreement_id:
            raise ValueError('INVALID_DISAGREEMENT')
        if actor not in ('RESEARCH',disagreement['payload']['owner']): raise PermissionError('DISAGREEMENT_OWNER_REQUIRED')
        if not evidence_ids or not reason.strip(): raise ValueError('RESOLUTION_EVIDENCE_REQUIRED')
        for aid in evidence_ids: self.require(pid,aid)
        result=self.store.create_artifact(pid,'DISAGREEMENT_RESOLUTION',
            {'disagreement_id':disagreement_id,'evidence_ids':evidence_ids,'reason':reason,'owner':actor},role=actor,
            dependencies=[self.store.dependency(aid) for aid in evidence_ids])
        return result.model_dump()

    def require_no_disagreement(self,pid):
        pending=self.store.latest(pid,'DISAGREEMENT')
        resolution=self.store.latest(pid,'DISAGREEMENT_RESOLUTION')
        if pending and (not resolution or not self.store.is_usable_input(resolution['artifact_id']) or
            resolution['payload']['disagreement_id']!=pending['artifact_id']): raise ValueError('DISAGREEMENT_UNRESOLVED')

    def fact_pack(self, pid: str, payload: dict, actor='RESEARCH'):
        if actor != 'RESEARCH':
            raise PermissionError('RESEARCH_ONLY_FACT_PACK')
        value = FactPack.model_validate(payload)
        if len({x.fact_id for x in value.facts}) != len(value.facts):
            raise ValueError('DUPLICATE_FACT_ID')
        ids = []
        for fact in value.facts:
            for sid in fact.source_ids:
                source = self.store.latest(pid, 'SOURCE_'+sid)
                if not source or source['payload']['status'] != 'AVAILABLE':
                    raise ValueError('FACT_SOURCE_MISSING:'+sid)
                self.require(pid, source['artifact_id'])
                ids.append(source['artifact_id'])
        from vnext.phase2.hardening.evidence import EvidenceIntegrity,strict
        integrity=EvidenceIntegrity(self.store)
        if strict(self.store,pid) or any(f.evidence_ids for f in value.facts):
            integrity.validate_facts(pid,value.facts)
            ids=[]
            for fact in value.facts:
                refs=[self.store.latest(pid,'EVIDENCE_'+eid) for eid in fact.evidence_ids]
                data=fact.model_dump();old=self.store.latest(pid,'FACT_'+fact.fact_id)
                if old and old['output_hash']==digest(data) and self.store.is_usable_input(old['artifact_id']):item=old
                else:item=self.store.create_artifact(pid,'FACT_'+fact.fact_id,data,role=actor,
                    dependencies=[self.store.dependency(ref['artifact_id']) for ref in refs]).model_dump()
                ids.append(item['artifact_id'])
        return self.store.create_artifact(pid, 'FACT_PACK', value.model_dump(), role=actor,
            dependencies=[self.store.dependency(x) for x in dict.fromkeys(ids)]).model_dump()

    def bound_script(self, pid: str, payload: dict, actor='SCRIPT_PRIMARY', extra_dependencies=None, run_metadata=None):
        if actor not in ('HUMAN','SCRIPT_PRIMARY','SCRIPT_EDITOR'):
            raise PermissionError('SCRIPT_OWNER_REQUIRED')
        value = BoundScript.model_validate(payload)
        previous=self.store.latest(pid,'SCRIPT')
        value.parent_script_artifact_id=previous['artifact_id'] if previous and actor in ('HUMAN','SCRIPT_EDITOR') else None
        if value.text != '\n'.join(x.text for x in value.segments):
            raise ValueError('SCRIPT_TEXT_SEGMENTS_MISMATCH')
        if len({x.segment_id for x in value.segments}) != len(value.segments):
            raise ValueError('DUPLICATE_SEGMENT_ID')
        pack = self.store.latest(pid, 'FACT_PACK')
        if not pack:
            raise ValueError('FACT_PACK_REQUIRED')
        self.require(pid, pack['artifact_id'], 'FACT_PACK')
        facts = {x['fact_id']:x for x in pack['payload']['facts']}
        for segment in value.segments:
            if segment.claim and not segment.fact_ids:
                raise ValueError('UNBOUND_CLAIM:'+segment.segment_id)
            for fid in segment.fact_ids:
                if fid not in facts or facts[fid]['support_status'] != 'SUPPORTED':
                    raise ValueError('FACT_NOT_SUPPORTED:'+fid)
            evidence = ' '.join(facts[fid]['statement'] for fid in segment.fact_ids)
            if segment.claim and set(numbers(segment.text))-set(numbers(evidence)):
                raise ValueError('NUMBER_MISMATCH:'+segment.segment_id)
        from vnext.phase2.hardening.evidence import EvidenceIntegrity,strict
        integrity=EvidenceIntegrity(self.store);claim_dependencies=[]
        if strict(self.store,pid) or value.contract_version==2:
            if value.contract_version!=2:raise ValueError('CLAIM_LEVEL_SCRIPT_REQUIRED')
            claim_dependencies=integrity.claims(pid,value,facts,actor)
        role=actor if actor!='HUMAN' else 'SCRIPT_PRIMARY' 
        supplied=[d for d in (extra_dependencies or []) if self.store.get_artifact(d.artifact_id)['artifact_type']=='EFFECTIVE_SKILL_SNAPSHOT_'+role]
        snapshot=self.require(pid,supplied[0].artifact_id) if supplied else self.snapshot(pid,role)
        deps=[self.store.dependency(pack['artifact_id']),self.store.dependency(snapshot['artifact_id']),
            *[self.store.dependency(aid) for aid in claim_dependencies],*(extra_dependencies or [])]
        if strict(self.store,pid):deps.append(self.store.dependency(self.store.latest(pid,'ARCHITECTURE_POLICY')['artifact_id']))
        deps=list({d.artifact_id:d for d in deps}.values())
        artifact = self.store.create_artifact(pid, 'SCRIPT', value.model_dump(), role=actor,
            dependencies=deps, **(run_metadata or {}))
        project = self.store.get_project(pid)
        project.h2_script_artifact_id = None
        if value.contract_version==2:integrity.coverage(pid,artifact.model_dump())
        project.state = 'SCRIPT_DRAFT'
        self.store.save_project(project)
        return artifact.model_dump()

    def humanize(self, pid: str, original_id: str, proposed: dict, extra_dependencies=None, run_metadata=None):
        original = self.store.get_artifact(original_id)
        if original['project_id']!=pid or not reusable_script(self.store,original_id):
            raise ValueError('STALE_OR_BLOCKED_INPUT')
        before = BoundScript.model_validate(original['payload'])
        proposed = {**proposed, 'semantic_status':'AUDIT_REQUIRED'}
        after = BoundScript.model_validate(proposed)
        diff = semantic_diff(before, after)
        after.semantic_diff = diff
        # No deterministic check can prove natural-language semantic equivalence.
        # Any changed prose still requires an independent audit before H2.
        if any(diff.values()):
            after.semantic_status = 'SEMANTIC_CHANGE_DETECTED'
            artifact = self.store.create_artifact(pid, 'SCRIPT', after.model_dump(), role='SCRIPT_EDITOR',
                dependencies=[*[self.store.dependency(x['artifact_id']) for x in original['dependencies']], *(extra_dependencies or [])], status='BLOCKED', **(run_metadata or {}))
            project = self.store.get_project(pid)
            project.h2_script_artifact_id = None
            self.store.save_project(project)
            return artifact.model_dump()
        return self.bound_script(pid, after.model_dump(), 'SCRIPT_EDITOR', extra_dependencies, run_metadata)


def numbers(text: str):
    return re.findall(r'\d+(?:\.\d+)?%?', text)


def reusable_script(store,artifact_id):
    """An earlier stage's script may be a historical parent of the canonical script.

    This is only for owner editing/resume, never for Audit, H2 or downstream production.
    Factual/skill dependencies must still be current and a blocked parent never qualifies.
    """
    item=store.get_artifact(artifact_id)
    if item['artifact_type']!='SCRIPT' or item['current_status'] in ('STALE','BLOCKED','FAILED'):return False
    if any(not store.is_usable_input(d['artifact_id']) for d in item['dependencies']):return False
    latest=store.latest(item['project_id'],'SCRIPT')
    seen=set()
    while latest and latest['artifact_id'] not in seen:
        if latest['artifact_id']==artifact_id:return True
        seen.add(latest['artifact_id'])
        parent=latest['payload'].get('parent_script_artifact_id')
        latest=store.get_artifact(parent) if parent else None
        if latest and latest['project_id']!=item['project_id']:return False
    return False


def semantic_diff(before: BoundScript, after: BoundScript):
    def polarity(text):
        return re.findall(r'不|没|无|禁止|允许|必须|不能|not\b|never\b|must\b', text, re.I)
    def entities(text):
        return re.findall(r'[A-Z][A-Za-z0-9_-]+|[“「].+?[”」]', text)
    return {'claim_units':[c.model_dump() for c in before.claim_units]!=[c.model_dump() for c in after.claim_units],
            'numbers':numbers(before.text)!=numbers(after.text),
            'entities':entities(before.text)!=entities(after.text),
            'polarity':polarity(before.text)!=polarity(after.text),
            'fact_bindings':[(s.segment_id,s.claim,s.fact_ids) for s in before.segments] !=
                            [(s.segment_id,s.claim,s.fact_ids) for s in after.segments],
            'claim_text':[(s.segment_id,s.text) for s in before.segments if s.claim] !=
                         [(s.segment_id,s.text) for s in after.segments if s.claim]}
