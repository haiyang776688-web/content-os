"""Incremental architecture hardening endpoints on the existing app."""
from fastapi import HTTPException,Request
from fastapi.responses import FileResponse
from vnext.phase2.api import DataIn
from vnext.phase2.hardening.evidence import EvidenceIntegrity,strict
from vnext.phase2.hardening.dependencies import Dependencies
from vnext.phase2.hardening.audio import AudioClock
from vnext.phase2.hardening.providers import matrix
from vnext.phase2.hardening.model_runs import ModelRuns
from vnext.phase2.hardening.voices import voices
from vnext.phase2.hardening.research import ResearchTools
from vnext.gateways.model.gateway import ModelGateway
from vnext.secrets.store import SecretStore

def attach(app,store,root):
    def checked(fn):
        try:return fn()
        except PermissionError as e:raise HTTPException(403,str(e)) from e
        except KeyError as e:raise HTTPException(404,str(e)) from e
        except Exception as e:raise HTTPException(400,str(e)) from e
    @app.get('/hardening.js')
    def js():return FileResponse(root/'vnext/apps/workbench/hardening.js',media_type='application/javascript')
    @app.get('/api/projects/{pid}/hardening')
    def state(pid:str):
        def read():
            p=store.get_project(pid)
            artifacts=store.artifacts(pid)
            return {'strict':strict(store,pid),'project':p.model_dump(),'providers':matrix(SecretStore(),store),
                'voices':voices(store),'model_runs':ModelRuns(store,ModelGateway()).rows(pid),
                'manifest':Dependencies(store).validate(pid),'artifacts':[a for a in artifacts if a['artifact_type'] in ('ARCHITECTURE_POLICY','CLAIM_COVERAGE_REPORT','CLAIM_COVERAGE_DECISION','AUDIO_TIMING_MAP','RESOLVED_VISUAL_COMPOSITION','PROJECT_DEPENDENCY_MANIFEST')],
                'state_semantics':[{'artifact_id':a['artifact_id'],'artifact_type':a['artifact_type'],'is_latest_revision':store.is_latest_revision(a['artifact_id']),'dependencies_valid':store.dependencies_valid(a['artifact_id']),'is_usable_input':store.is_usable_input(a['artifact_id'])} for a in artifacts if store.is_latest_revision(a['artifact_id'])]}
        return checked(read)
    @app.post('/api/projects/{pid}/hardening/enable')
    def enable(pid:str,value:DataIn):return checked(lambda:EvidenceIntegrity(store).enable(pid,value.actor))
    @app.post('/api/projects/{pid}/hardening/evidence')
    def evidence(pid:str,value:DataIn):return checked(lambda:EvidenceIntegrity(store).evidence(pid,value.payload,value.actor))
    @app.post('/api/projects/{pid}/hardening/claim-decision')
    def decision(pid:str,value:DataIn):return checked(lambda:EvidenceIntegrity(store).decide(pid,value.payload['report_id'],value.payload['decisions'],value.actor,value.payload['reviewer']))
    @app.post('/api/projects/{pid}/hardening/audio-timing')
    def audio(pid:str,value:DataIn):return checked(lambda:AudioClock(store).create(pid,value.payload,value.actor))
    @app.post('/api/projects/{pid}/hardening/manifest')
    def manifest(pid:str,value:DataIn):
        if value.actor!='HUMAN':raise HTTPException(403,'MANIFEST_HUMAN_REQUIRED')
        return checked(lambda:Dependencies(store).build(pid))
    @app.post('/api/projects/{pid}/hardening/relink')
    def relink(pid:str,value:DataIn):return checked(lambda:Dependencies(store).relink(pid,value.payload['asset_id'],value.payload['path'],value.actor))
    @app.post('/api/projects/{pid}/hardening/research-tool')
    def research(pid:str,value:DataIn):return checked(lambda:ResearchTools(store).invoke(pid,value.payload,value.actor))
