"""Download endpoints return the artifact belonging to the selected project."""
import importlib
import zipfile

from fastapi.testclient import TestClient


def test_render_and_jianying_download_are_scoped_and_real(tmp_path, monkeypatch):
    monkeypatch.setenv('CONTENT_OS_DATA', str(tmp_path))
    from vnext.apps.workbench import server
    server = importlib.reload(server)
    store = server.store
    project = store.create_project('delivery')
    other = store.create_project('other')
    pid = project.project_id
    root = tmp_path / 'projects' / pid
    root.mkdir(parents=True, exist_ok=True)
    movie = root / 'final.mp4'
    movie.write_bytes(b'video test bytes')
    render = store.create_artifact(pid, 'RENDER', {'preview_path': str(movie), 'media_type': 'video/mp4'}, role='RENDER')
    transfer = root / 'jianying_exports' / 'EXP-test'
    native = transfer / 'ContentOS-EXP-test'
    native.mkdir(parents=True)
    (transfer / 'transfer_manifest.json').write_text('{}')
    (transfer / 'JIANYING_EXPORT_REPORT.json').write_text('{}')
    (native / 'draft_content.json').write_text('{}')
    exported = store.create_artifact(pid, 'EXPORT', {'path': str(transfer), 'native_draft_path': str(native)}, role='EXPORT')

    with TestClient(server.app) as client:
        video = client.get(f'/api/projects/{pid}/render/{render.artifact_id}/download')
        assert video.status_code == 200 and video.content == b'video test bytes'
        assert 'attachment' in video.headers['content-disposition']
        assert client.get(f'/api/projects/{other.project_id}/render/{render.artifact_id}/download').status_code == 404

        archive = client.get(f'/api/projects/{pid}/jianying/export/{exported.artifact_id}/download')
        assert archive.status_code == 200 and archive.content[:2] == b'PK'
        assert 'attachment' in archive.headers['content-disposition']
        with zipfile.ZipFile(tmp_path / 'projects' / pid / 'deliveries' / (exported.artifact_id + '.zip')) as bundle:
            names = set(bundle.namelist())
        assert {'transfer/transfer_manifest.json', 'transfer/JIANYING_EXPORT_REPORT.json',
                'transfer/ContentOS-EXP-test/draft_content.json', 'README.txt'} <= names
        assert client.get(f'/api/projects/{other.project_id}/jianying/export/{exported.artifact_id}/download').status_code == 404
