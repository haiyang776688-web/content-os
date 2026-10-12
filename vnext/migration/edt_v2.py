"""Lossless schema upgrade; never infer scene/fact bindings or overwrite history."""
import argparse
import json
from pathlib import Path
from vnext.contracts import EDT
from vnext.storage.store import digest


def upgrade_edt(value: dict, bindings: dict | None = None) -> tuple[dict, dict]:
    before=EDT.model_validate(value)
    if before.schema_version!=1:raise ValueError('EDT_V1_REQUIRED')
    result=before.model_copy(deep=True)
    result.schema_version=2
    result.revision+=1
    bindings=bindings or {}
    known={c.clip_id for c in result.clips}
    if set(bindings)-known:raise ValueError('UNKNOWN_CLIP_BINDING')
    fields={'scene_id','beat_id','ir_node_id','pattern_id'}
    for clip in result.clips:
        mapping=bindings.get(clip.clip_id,{})
        if set(mapping)-fields:raise ValueError('SEMANTIC_BINDING_FIELDS_ONLY')
        for key,val in mapping.items():setattr(clip,key,val)
        clip.origin='MIGRATED_V1'
        clip.edit_source='MIGRATION'
    after=EDT.model_validate(result.model_dump()).model_dump()
    return after,{'migration':'EDT_V1_TO_V2','input_hash':digest(value),'output_hash':digest(after),
        'source_ranges_preserved':True,'timeline_ranges_preserved':True,
        'bindings_supplied_by_owner':bool(bindings),
        'unbound_clip_ids':[c.clip_id for c in result.clips if not c.beat_id],
        'limitation':'No script, fact, scene, beat or pattern semantics inferred. Historical input must be retained.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--bindings')
    args=p.parse_args();destination=Path(args.output)
    if destination.exists() or destination.with_suffix('.migration.json').exists():raise ValueError('OUTPUT_ALREADY_EXISTS')
    source=json.loads(Path(args.input).read_text())
    binding=json.loads(Path(args.bindings).read_text()) if args.bindings else None
    result,report=upgrade_edt(source,binding)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    destination.with_suffix('.migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
