"""Append-only attempt ledger with transactional budget reservations."""
import json,math,time,uuid
from vnext.contracts import utc_now
from vnext.storage.store import canonical
from vnext.phase2.hardening.contracts import ModelRunLedger
from vnext.phase2.hardening.providers import adapter_caps,record_live,truth

class ModelRuns:
    def __init__(self,store,gateway):self.store,self.gateway=store,gateway
    def rows(self,pid):
        with self.store.connection() as db:
            if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_runs'").fetchone():return []
            return [json.loads(r['data']) for r in db.execute('SELECT data FROM model_runs WHERE project_id=? ORDER BY rowid',(pid,))]
    def write(self,row,db=None):
        row=ModelRunLedger.model_validate(row).model_dump()
        def put(conn):
            conn.execute('CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY,project_id TEXT,at TEXT,data TEXT)')
            conn.execute('INSERT INTO model_runs VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(row['run_id'],row['project_id'],row['at'],json.dumps(row)))
            path=self.store.root/'projects'/row['project_id']/'model_run_ledger.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('ab') as f:f.write(canonical(row)+b'\n')
        if db is not None:put(db)
        else:
            with self.store.connection() as conn:put(conn)
        return row
    def reserve(self,pid,request,worker,attempt,fallback,zero=False):
        p=self.store.get_project(pid);pricing=p.model_pricing.get(worker.worker_id,{})
        blocks=request.content_blocks+[b for m in request.messages if isinstance(m.content,list) for b in m.content]
        counts={k:sum(b.type==k for b in blocks) for k in ('IMAGE','AUDIO','VIDEO')}
        text=request.system_prompt+str([m.model_dump() for m in request.messages])
        n=len(text.encode())+attempt*700 # conservative heuristic, explicitly estimated
        out=int(request.config.get('max_output_tokens',pricing.get('max_output_tokens',4096)))
        cost=0.0 if zero else None
        if pricing and not zero:
            cost=(n*pricing['input_per_million']+out*pricing['output_per_million'])/1e6+sum(counts[k]*pricing.get(k.lower()+'_per_input',0) for k in counts)
            if any(counts[k] and k.lower()+'_per_input' not in pricing for k in counts):cost=None
        row=ModelRunLedger(run_id='RUN-'+uuid.uuid4().hex[:16],project_id=pid,stage=request.config.get('stage',request.role.value),role=request.role.value,
            provider=worker.provider,provider_id=worker.worker_id,model_id=self.gateway.secrets.get(worker.model_env or '') or worker.model,model=self.gateway.secrets.get(worker.model_env or '') or worker.model,
            input_tokens=None,estimated_cost=cost,cost_status='ESTIMATED' if cost is not None else 'UNKNOWN',
            image_inputs=counts['IMAGE'],audio_inputs=counts['AUDIO'],video_inputs=counts['VIDEO'],retry_count=attempt,
            status='RESERVED',at=utc_now(),fallback_from=fallback,metadata={'preflight_input_tokens_estimate':n,'max_output_tokens':out,'pricing':pricing}).model_dump()
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY,project_id TEXT,at TEXT,data TEXT)')
            prior=[json.loads(r['data']) for r in db.execute('SELECT data FROM model_runs WHERE project_id=?',(pid,))]
            def spend(rows):return sum(r['actual_cost'] if r['actual_cost'] is not None else r['estimated_cost'] or 0 for r in rows if r['status']!='BLOCKED' and not r['cache_hit'])
            error=None
            from vnext.providers.settings import Settings
            policy=Settings(self.store.root).project_policy(pid)['cost_unknown_policy']
            if cost is None and policy=='BLOCK':error='COST_UNKNOWN_BLOCKED'
            if cost is None and policy=='ASK' and not request.config.get('cost_confirmed'):error='COST_UNKNOWN_APPROVAL_REQUIRED'
            if any(v is not None for v in p.budget.values()) and cost is None:error='BUDGET_ESTIMATE_UNAVAILABLE'
            if p.budget.get('daily') is not None and any(r['actual_cost'] is None and r['estimated_cost'] is None and r['status']!='BLOCKED' and r['at'][:10]==row['at'][:10] for r in prior):error='BUDGET_SPEND_UNKNOWN'
            if p.budget.get('project') is not None and any(r['actual_cost'] is None and r['estimated_cost'] is None and r['status']!='BLOCKED' for r in prior):error='BUDGET_SPEND_UNKNOWN'
            limits={'single_run':0,'project':spend(prior),'daily':spend([r for r in prior if r['at'][:10]==row['at'][:10]])}
            for key,total in limits.items():
                if p.budget.get(key) is not None and cost is not None and total+cost>p.budget[key]:error='BUDGET_'+key.upper()+'_EXCEEDED'
            if error:row['status']='BLOCKED';row['metadata']['error']=error
            self.write(row,db)
        if error:raise RuntimeError(error)
        return row
    def finish(self,row,started,raw=None,error=None,cache=False):
        usage=(raw or {}).get('usage',{});pricing=row['metadata']['pricing']
        row.update(status='FAILED' if error else 'COMPLETED',latency=time.monotonic()-started,cache_hit=cache,
            input_tokens=usage.get('prompt_tokens',usage.get('input_tokens')),output_tokens=usage.get('completion_tokens',usage.get('output_tokens')),
            cached_tokens=usage.get('prompt_tokens_details',{}).get('cached_tokens',usage.get('cached_tokens')))
        actual=usage.get('cost')
        # Only an explicit provider monetary value counts as actual; rate calculations remain estimates.
        if isinstance(actual,(int,float)) and actual>=0 and usage.get('currency')==row['currency']:row.update(actual_cost=actual,cost_status='ACTUAL')
        elif pricing and row['input_tokens'] is not None and row['output_tokens'] is not None:
            row['estimated_cost']=(row['input_tokens']*pricing['input_per_million']+row['output_tokens']*pricing['output_per_million'])/1e6+sum(row[k.lower()+'_inputs']*pricing.get(k.lower()+'_per_input',0) for k in ('IMAGE','AUDIO','VIDEO'))
            row['cost_status']='ESTIMATED'
        if error:
            from vnext.secrets.secure import redact
            row['metadata']['error']=redact(str(error))
        return self.write(row)
    def invoke(self,pid,request):
        from vnext.registries.catalog import WORKERS,ROLE_CONTRACTS
        from vnext.contracts import ProviderProtocol as P
        required={x.value for x in ROLE_CONTRACTS[request.role].required_capabilities}
        if request.tools:required.add('TOOL_CALLING')
        for b in request.content_blocks:
            if b.type in ('VIDEO','IMAGE','AUDIO'):required.add(b.type+'_INPUT')
        from vnext.registries.catalog import SOURCE_BOUNDARY
        if 'UNTRUSTED_SOURCE_DATA' not in request.system_prompt:request=request.model_copy(update={'system_prompt':request.system_prompt+SOURCE_BOUNDARY})
        original=request.worker_profile;p=self.store.get_project(pid)
        candidates=[original]
        if p.fallback_policy=='AUTO_SAFE' or (p.fallback_policy=='ASK' and request.config.get('fallback_confirmed')):
            candidates+=p.fallback_workers
        seen=set();last=None
        for wid in candidates:
            if wid in seen or wid not in WORKERS:continue
            seen.add(wid);worker=WORKERS[wid];caps=set(adapter_caps(worker,self.gateway.secrets))
            error=None
            if wid.startswith('custom_') and request.config.get('stage')!='PROVIDER_PROBE':caps &= set(truth(worker,self.gateway.secrets).get('verified_capabilities',[]))
            if not required<=caps:error='ADAPTER_CAPABILITY_UNSUPPORTED:'+','.join(sorted(required-caps))
            if not truth(worker,self.gateway.secrets)['configured']:error='PROVIDER_NOT_CONFIGURED'
            if wid!=original and worker.protocol==P.MOCK and WORKERS[original].protocol!=P.MOCK:error='LIVE_TO_MOCK_FALLBACK_FORBIDDEN'
            from vnext.providers.settings import Settings,ROOT,privacy
            local=privacy(self.gateway.secrets.get(worker.endpoint_env or '') or '')=='LOCAL'
            if worker.protocol!=P.MOCK and p.privacy_mode=='LOCAL_ONLY' and not local:error='LOCAL_ONLY_MODEL_UPLOAD_FORBIDDEN'
            if worker.protocol!=P.MOCK and not local and p.privacy_mode=='ASK_BEFORE_UPLOAD' and not request.config.get('upload_confirmed'):error='UPLOAD_CONFIRMATION_REQUIRED'
            rates=p.model_pricing.get(wid,{})
            cfg={**request.config,'max_output_tokens':int(request.config.get('max_output_tokens',rates.get('max_output_tokens',4096)))}
            r=request.model_copy(update={'worker_profile':wid,'config':cfg})
            if error:
                row=self.reserve(pid,r,worker,0,original if wid!=original else None,zero=True);row['status']='BLOCKED';row['metadata']['error']=error;self.write(row);last=RuntimeError(error);continue
            try:
                attempt_rows=[]
                def attempt(fn,index):
                    row=self.reserve(pid,r,worker,index,original if wid!=original else None);started=time.monotonic();raw=None;attempt_rows.append(row['run_id'])
                    try:
                        raw=fn()
                        self.gateway._parse(raw['choices'][0]['message']['content'] or '',r.response_schema)
                        self.finish(row,started,raw);return raw
                    except Exception as e:self.finish(row,started,raw,error=e);raise
                def synthetic(result,cache):
                    row=self.reserve(pid,r,worker,0,original if wid!=original else None,zero=True)
                    self.finish(row,time.monotonic(),{'usage':{}},cache=cache)
                from vnext.gateways.model.gateway import EXECUTION_HOOKS
                token=EXECUTION_HOOKS.set((attempt,synthetic))
                try:result=self.gateway.invoke(r)
                finally:EXECUTION_HOOKS.reset(token)
                if not result.provider_metadata.get("cache_hit"):record_live(self.store,worker,self.gateway.secrets,result)
                return result.model_copy(update={'provider_metadata':{**result.provider_metadata,'run_id':attempt_rows[-1] if attempt_rows else None,'provider_id':wid,'model_id':result.provider_metadata.get('model'),'selected_worker':wid,'fallback_from':original if wid!=original else None}})
            except Exception as e:
                last=e
                if worker.protocol==P.MOCK:
                    row=self.reserve(pid,r,worker,0,original if wid!=original else None,zero=True);self.finish(row,time.monotonic(),error=e)
                if str(e).startswith(('BUDGET_','UPLOAD_','LOCAL_ONLY')):raise
        if p.fallback_policy=='ASK' and not request.config.get('fallback_confirmed') and p.fallback_workers:
            raise RuntimeError('FALLBACK_HUMAN_APPROVAL_REQUIRED:'+str(last))
        raise last or RuntimeError('NO_COMPATIBLE_FALLBACK')

def governed(gateway,store,pid,request):
    from vnext.gateways.model.gateway import ModelGateway
    if isinstance(gateway,ModelGateway):return ModelRuns(store,gateway).invoke(pid,request)
    # Dependency-injected test adapter is explicitly a fixture; never provider proof.
    result=gateway.invoke(request)
    store.event(pid,'TEST_ADAPTER_INVOKED',live_verified=False)
    return result
