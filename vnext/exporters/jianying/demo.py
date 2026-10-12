"""Generate an editable native diagnostic draft using only bundled test media."""
from pathlib import Path
import json
import os

from vnext.core.editing import Editing
from vnext.core.runtime import Runtime
from vnext.exporters.jianying.adapter import JianyingExporter
from vnext.media.library.service import MediaLibrary
from vnext.storage.store import Store


def main():
    root = Path(__file__).resolve().parents[3]
    media = root / 'examples/jianying_source_media'
    if not media.is_dir():
        raise SystemExit('Bundled diagnostic media missing')
    store = Store(Path(os.environ.get('CONTENT_OS_DATA') or root / 'data'))
    pid = store.create_project('Jianying native diagnostic').project_id
    editing = Editing(store)
    script = editing.script(pid, 'Diagnostic test pattern and test tone, not production content')
    Runtime(store).approve_h2(pid, script['artifact_id'])
    assets = MediaLibrary(store).add_folder(pid, media)
    video = next(x for x in assets if x.type == 'VIDEO')
    audio = next(x for x in assets if x.type == 'AUDIO')
    editing.create_timeline(pid)
    for clip in [
        dict(track='VIDEO', asset_id=video.asset_id, source_in=2, source_out=4, timeline_out=2),
        dict(track='VOICE', asset_id=audio.asset_id, source_in=1, source_out=3, timeline_out=2),
        dict(track='TEXT', metadata={'text': 'Content OS editable title'}, source_out=4, timeline_out=4, position={'x': .5, 'y': .3}),
        dict(track='SUBTITLE', metadata={'text': '可编辑字幕验收'}, source_out=2, timeline_out=2, position={'x': .5, 'y': .8})]:
        edt = editing.edit_timeline(pid, 'ADD', clip)
    print(json.dumps(JianyingExporter(store).export_transfer_bundle(pid, edt['artifact_id']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
