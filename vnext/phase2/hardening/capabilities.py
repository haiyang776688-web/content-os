"""Build-blocking prerequisites are separate from consumption and integration."""
import json
from graphlib import TopologicalSorter
from pathlib import Path

PRIMITIVES = {'PRIM-STORAGE':'Immutable artifacts and SQLite',
 'PRIM-OWNERSHIP':'Single writer / edit commands',
 'PRIM-UI':'Workbench shell', 'PRIM-RENDER':'Remotion rendering interface',
 'PRIM-REGISTRY':'Versioned pack registry'}
PREREQUISITES = {
 1:['PRIM-STORAGE'],2:['CAP-001'],3:['CAP-001'],4:['CAP-001'],5:['CAP-007'],
 6:['CAP-001'],7:['PRIM-STORAGE'],8:['PRIM-STORAGE'],9:['CAP-008'],
 10:['CAP-012'],11:['PRIM-REGISTRY'],12:['CAP-007','CAP-008','CAP-009','CAP-011'],
 13:['CAP-012'],14:['PRIM-STORAGE','PRIM-OWNERSHIP'],15:['CAP-007'],
 16:['PRIM-STORAGE'],17:['CAP-013','PRIM-RENDER'],18:['CAP-013','CAP-022'],
 19:['CAP-018'],20:['CAP-017','CAP-018'],21:['CAP-013'],
 22:['PRIM-STORAGE','CAP-014'],23:['CAP-013','PRIM-RENDER'],24:['PRIM-UI'],25:['PRIM-STORAGE','PRIM-UI'],26:['CAP-025','CAP-028','CAP-007'],27:['CAP-025','CAP-013'],28:['CAP-025']}
INTEGRATIONS={3:[9,11],5:[6],6:[7,12,16],9:[12],10:[13,14],11:[22],13:[14,22],
 14:[12,13,22],15:[13],16:[6,13],17:[22,23],18:[17,23],19:[20],20:[19,21,22],
 21:[22],22:[11,18,20,21,23],23:[22,17,20],24:list(range(1,24))}
OPTIONAL={15:[19],19:[],20:[19,21],21:[],23:[19]}


def graph(entries):
    nodes={x['capability_id']:set(x['prerequisites']) for x in entries}
    nodes.update({key:set() for key in PRIMITIVES})
    for key,deps in nodes.items():
        if key in deps:raise ValueError('CAPABILITY_SELF_DEPENDENCY')
        if not deps<=nodes.keys():raise ValueError('UNKNOWN_PREREQUISITE')
    return nodes


def ready_blockers(entry,availability):
    # consumers, integrates_with and optional_integrations never participate.
    return [key for key in entry['prerequisites'] if not availability.get(key,False)]


def migrate(root,roadmap_file="CAPABILITY_ROADMAP.json",graph_file="DEPENDENCY_GRAPH.json"):
    root=Path(root);path=root/roadmap_file;road=json.loads(path.read_text())
    entries=road['capabilities']
    for item in entries:
        n=int(item['capability_id'].split('-')[-1]);item.pop('dependencies',None)
        item['prerequisites']=PREREQUISITES[n]
        item['integrates_with']=[f'CAP-{i:03}' for i in INTEGRATIONS.get(n,[])]
        item['optional_integrations']=[f'CAP-{i:03}' for i in OPTIONAL.get(n,[])]
        item['consumers']=[]
    for item in entries:
        for prereq in item['prerequisites']:
            owner=next((x for x in entries if x['capability_id']==prereq),None)
            if owner:owner['consumers'].append(item['capability_id'])
    order=list(TopologicalSorter(graph(entries)).static_order())
    road.update(release='Phase 2 Architecture Hardening' if road.get('architecture_hardening',{}).get('completed') else 'Phase 2 Architecture Hardening (in progress)',phase2_complete=False,
        relation_semantics='Only prerequisites block construction; consumers and integrations are descriptive.')
    path.write_text(json.dumps(road,ensure_ascii=False,indent=2)+'\n')
    result={'schema_version':1,'is_dag':True,'primitive_nodes':PRIMITIVES,
        'build_order':order,'capabilities':[{k:x[k] for k in ['capability_id','prerequisites','consumers','integrates_with','optional_integrations']} for x in entries]}
    (root/graph_file).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
