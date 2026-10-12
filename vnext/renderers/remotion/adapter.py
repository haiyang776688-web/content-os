"""EDT -> Remotion props. EDT remains the timeline source of truth."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from vnext.contracts import EDT
from vnext.core.preflight import check
from vnext.media.library.service import MediaLibrary
from vnext.storage.store import Store


class RemotionAdapter:
    def __init__(self, root: Path, store: Store):
        self.root = Path(root)
        self.store = store
        self.project = self.root / "vnext/renderers/remotion/project"

    @staticmethod
    def _browser_args() -> list[str]:
        configured = os.environ.get("REMOTION_BROWSER_EXECUTABLE")
        candidates = [configured, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                      shutil.which("google-chrome"), shutil.which("chromium")]
        executable = next((value for value in candidates if value and Path(value).is_file()), None)
        return ["--browser-executable", executable] if executable else []

    def prepare(self, project_id: str, edt_artifact_id: str, *, purpose="FORMAL") -> dict:
        validation = check(self.store, project_id, edt_artifact_id,require_audio=purpose=="FORMAL")
        if not validation["ok"]:
            raise ValueError("PREFLIGHT_FAILED:" + ",".join(validation["issues"]))
        from vnext.renderers.remotion.resolver import CompositionResolver
        resolved = CompositionResolver(self.root,self.store).resolve(project_id,edt_artifact_id)
        props = resolved['props']
        run_id = "RUN-" + uuid.uuid4().hex[:10]
        props_path = self.store.root / "projects" / project_id / "renders" / (run_id + "-props.json")
        props_path.parent.mkdir(parents=True, exist_ok=True)
        props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2) + "\n")
        return {"run_id": run_id, "props_path": str(props_path), "props": props,
            "composition_fingerprint": resolved["fingerprint"],
            "timing_provenance": props.get("timing_provenance", {"timing_mode":"CURRENT","fallback_used":False})}

    def still(self, project_id: str, edt_artifact_id: str) -> dict:
        prepared = self.prepare(project_id, edt_artifact_id)
        output = self.store.root / "projects" / project_id / "renders" / (prepared["run_id"] + ".png")
        result = subprocess.run(["npx", "remotion", "still", "src/index.tsx", "ContentOSPreview", str(output),
                                 "--props", prepared["props_path"], "--frame", "0", *self._browser_args()],
                                cwd=self.project, capture_output=True, text=True, timeout=120)
        if result.returncode != 0 or not output.exists():
            raise RuntimeError("REMOTION_STILL_FAILED:" + result.stderr[-500:])
        artifact = self.store.create_artifact(project_id, "RENDER", {"preview_path": str(output),
            "renderer": "REMOTION", "media_type": "image/png", "run_id": prepared["run_id"], "props_path": prepared["props_path"],
            "timing_provenance":prepared["timing_provenance"]}, role="RENDER",
            dependencies=[self.store.dependency(edt_artifact_id)])
        return artifact.model_dump(mode="json")

    def video(self, project_id: str, edt_artifact_id: str) -> dict:
        if self.store.get_project(project_id).phase2_enabled:
            from vnext.phase2.production import Production, mechanical
            Production(self.store).require_storyboard(project_id)
            report=mechanical(self.store,project_id,edt_artifact_id,require_voice=True)
            if report['verdict']=='FAIL': raise ValueError('MECHANICAL_QA_VETO')
        prepared = self.prepare(project_id, edt_artifact_id)
        output = self.store.root / "projects" / project_id / "renders" / (prepared["run_id"] + ".mp4")
        result = subprocess.run(["npx", "remotion", "render", "src/index.tsx", "ContentOSPreview", str(output),
                                 "--props", prepared["props_path"], "--codec", "h264", "--concurrency", "2", *self._browser_args()],
                                cwd=self.project, capture_output=True, text=True, timeout=300)
        if result.returncode != 0 or not output.exists():
            raise RuntimeError("REMOTION_VIDEO_FAILED:" + result.stderr[-500:])
        artifact = self.store.create_artifact(project_id, "RENDER", {"preview_path": str(output),
            "renderer": "REMOTION", "media_type": "video/mp4", "run_id": prepared["run_id"],
            "props_path": prepared["props_path"], "timing_provenance":prepared["timing_provenance"]}, role="RENDER",
            dependencies=[self.store.dependency(edt_artifact_id)])
        return artifact.model_dump(mode="json")

    def storyboard_motion(self, project_id: str, edt_artifact_id: str) -> dict:
        """Review animation before the human storyboard gate; never a formal render."""
        from vnext.phase2.production import mechanical
        if mechanical(self.store,project_id,edt_artifact_id,require_voice=True)['verdict']=='FAIL':
            raise ValueError('MECHANICAL_QA_VETO')
        prepared=self.prepare(project_id,edt_artifact_id,purpose='STORYBOARD')
        output=self.store.root/'projects'/project_id/'storyboards'/(prepared['run_id']+'-motion.mp4')
        output.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(['npx','remotion','render','src/index.tsx','ContentOSPreview',str(output),
            '--props',prepared['props_path'],'--codec','h264','--concurrency','2',*self._browser_args()],
            cwd=self.project,capture_output=True,text=True,timeout=300)
        if result.returncode or not output.is_file():raise RuntimeError('STORYBOARD_MOTION_FAILED:'+result.stderr[-250:])
        return self.store.create_artifact(project_id,'STORYBOARD_MOTION',{
            'preview_path':str(output),'media_type':'video/mp4','purpose':'STORYBOARD_REVIEW',
            'formal_render':False,'run_id':prepared['run_id'],'props_path':prepared['props_path'],
            'composition_fingerprint':prepared['composition_fingerprint']},role='STORYBOARD',
            dependencies=[self.store.dependency(edt_artifact_id)]).model_dump()
