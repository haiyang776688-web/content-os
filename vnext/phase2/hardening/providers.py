"""Adapter truth, independent of a vendor's advertised capabilities."""
import json
from vnext.contracts import ProviderProtocol as P, utc_now

ALL_CAPS=['TEXT','STRUCTURED_OUTPUT','VISION','IMAGE_INPUT','VIDEO_INPUT','AUDIO_INPUT','TOOL_CALLING','STREAMING','REASONING','JSON_SCHEMA']

def adapter_caps(worker,secrets):
    from vnext.providers.settings import Settings,ROOT
    configured=Settings().configs().get(worker.worker_id) if ROOT is not None and isinstance(secrets,__import__('vnext.secrets.store',fromlist=['SecretStore']).SecretStore) else None
    if configured and configured['protocol']!='OPENAI_COMPATIBLE':return []
    if configured and not configured['enabled']:return []
    if worker.protocol==P.MOCK:return ['TEXT','STRUCTURED_OUTPUT','VISION','IMAGE_INPUT','VIDEO_INPUT','AUDIO_INPUT']
    if worker.protocol not in (P.OPENAI_CHAT,P.CUSTOM_OPENAI_COMPATIBLE):return []
    caps=['TEXT','STRUCTURED_OUTPUT'] # schema checked locally; not provider-native JSON_SCHEMA
    if worker.worker_id=='MINIMAX' and secrets.get(worker.model_env or '')=='MiniMax-M3':caps+=['VISION','IMAGE_INPUT','VIDEO_INPUT']
    return caps

def truth(worker,secrets,probe=None):
    mock=worker.protocol==P.MOCK;caps=adapter_caps(worker,secrets)
    configured=mock or all(secrets.configured(x) for x in (worker.endpoint_env,worker.api_key_env,worker.model_env))
    from vnext.providers.settings import Settings,ROOT
    settings=Settings().public(worker.worker_id) if ROOT is not None and isinstance(secrets,__import__('vnext.secrets.store',fromlist=['SecretStore']).SecretStore) and worker.worker_id in Settings().configs() else None
    if settings:configured=settings['configured']
    model=secrets.get(worker.model_env or '') or worker.model
    probe=probe or {}
    bound=probe.get('model')==model and probe.get('endpoint')==secrets.get(worker.endpoint_env or '')
    result={'registered':True,'configured':configured,'adapter_implemented':bool(caps),
        'credentials_available':mock or secrets.configured(worker.api_key_env),'model_discovered':bool(bound and probe.get('model_discovered')),
        'capability_verified':bool(bound and probe.get('verified_capabilities')),
        'verified_capabilities':probe.get('verified_capabilities',[]) if bound else [],
        'live_verified':bool(not mock and bound and probe.get('live_verified')),
        'last_probe_at':probe.get('at'),'last_probe_result':{k:v for k,v in probe.items() if k!='endpoint'} or None,'mock_only':mock,
        'adapter_capabilities':caps,'capability_matrix':{c:c in caps for c in ALL_CAPS}}
    if settings:
        result.update({k:settings[k] for k in ('configured','live_verified','connection_verified','model_verified','capability_verified','verified_capabilities','last_probe_at','last_probe_result','secret_source','privacy_classification')})
    return result

def matrix(secrets,store=None):
    from vnext.registries.catalog import WORKERS
    probes=store.root/'provider_probes.json' if store else None
    data=json.loads(probes.read_text()) if probes and probes.exists() else {}
    return {w.worker_id:{'worker_id':w.worker_id,'provider':w.provider,'protocol':w.protocol.value,
        'model':secrets.get(w.model_env or '') or w.model,**truth(w,secrets,data.get(w.worker_id))} for w in WORKERS.values()}

def record_live(store,worker,secrets,result):
    if worker.protocol==P.MOCK:return
    # A successful text request verifies only capabilities exercised by this request.
    path=store.root/'provider_probes.json'
    with store.lock:
        values=json.loads(path.read_text()) if path.exists() else {}
        values[worker.worker_id]={'at':utc_now(),'model':result.provider_metadata.get('model'),
            'endpoint':secrets.get(worker.endpoint_env or ''),'model_discovered':False,
            'verified_capabilities':result.provider_metadata.get('exercised_capabilities',['TEXT']),
            'live_verified':True,'result':'CALL_SUCCEEDED'}
        path.write_text(json.dumps(values,ensure_ascii=False,indent=2))
