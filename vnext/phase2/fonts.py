"""Local-only font registry and content-addressed project font dependencies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont
from vnext.phase2.contracts import FontRecord, TypographyProfile
from vnext.storage.store import Store, canonical, digest


def sha(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


class Fonts:
    def __init__(self, store: Store):
        self.store = store
        self.cache = store.root/'font_cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        with store.connection() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS fonts(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS font_files(path TEXT PRIMARY KEY, size INTEGER, mtime INTEGER, hash TEXT);
                CREATE TABLE IF NOT EXISTS font_scan_events(id INTEGER PRIMARY KEY, data TEXT);''')

    def list(self, query='', source='', classification=''):
        with self.store.connection() as db:
            rows = db.execute('SELECT data FROM fonts').fetchall()
        items = [json.loads(r['data']) for r in rows]
        with self.store.connection() as db:
            files={r['path']:dict(r) for r in db.execute('SELECT * FROM font_files')}
        for item in items:
            source_path=Path(item['file_path'])
            cached=files.get(item['file_path'])
            if not source_path.is_file():item['status']='MISSING'
            elif cached:
                stat=source_path.stat()
                if cached['hash']!=item['file_hash']:item['status']='CHANGED'
                elif cached['size']!=stat.st_size or cached['mtime']!=stat.st_mtime_ns:item['status']='RESCAN_REQUIRED'
        return sorted([x for x in items if query.casefold() in (x['family']+' '+x['full_name']).casefold()
            and (not source or x['source']==source)
            and (not classification or classification in x['classification'])],
            key=lambda x:(x['family'].casefold(), x['weight'], x['style'], x['face_index']))

    def get(self, font_id):
        with self.store.connection() as db:
            row = db.execute('SELECT data FROM fonts WHERE id=?',(font_id,)).fetchone()
        if not row:
            raise KeyError('FONT_NOT_FOUND')
        return FontRecord.model_validate_json(row['data'])

    def scan(self, paths: list[str] | None = None, source='SYSTEM'):
        if source not in ('SYSTEM','USER','PROJECT'):
            raise ValueError('INVALID_FONT_SOURCE')
        roots = [Path(x).expanduser().resolve() for x in paths] if paths else [
            Path('/System/Library/Fonts'),Path('/Library/Fonts'),Path.home()/'Library/Fonts']
        result = {'discovered':0,'cached':0,'errors':[],'roots':[]}
        for root in roots:
            root_state = {'path':str(root),'status':'EMPTY','count':0}
            if not root.exists():
                root_state['status']='NOT_FOUND'
                result['roots'].append(root_state)
                continue
            try:
                paths_in_root = [root] if root.is_file() else sorted(root.rglob('*'))
                for path in paths_in_root:
                    if not path.is_file() or path.suffix.lower() not in ('.ttf','.otf','.ttc','.otc'):
                        continue
                    root_state['count'] += 1
                    root_state['status'] = 'AVAILABLE'
                    stat = path.stat()
                    with self.store.connection() as db:
                        prev = db.execute('SELECT * FROM font_files WHERE path=?',(str(path),)).fetchone()
                    if prev and prev['size']==stat.st_size and prev['mtime']==stat.st_mtime_ns:
                        result['cached'] += 1
                        continue
                    try:
                        file_hash = sha(path)
                        count = 1
                        if path.suffix.lower() in ('.ttc','.otc'):
                            collection = TTCollection(str(path), lazy=True)
                            count = len(collection.fonts)
                            collection.close()
                        origin = 'USER' if Path.home() in path.parents else source
                        for index in range(count):
                            record = self._metadata(path,file_hash,index,origin)
                            with self.store.connection() as db:
                                db.execute('INSERT INTO fonts VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                                    (record.font_id, record.model_dump_json()))
                            result['discovered'] += 1
                        with self.store.connection() as db:
                            db.execute('INSERT OR REPLACE INTO font_files VALUES (?,?,?,?)',
                                (str(path), stat.st_size, stat.st_mtime_ns, file_hash))
                    except PermissionError:
                        root_state['status'] = 'PERMISSION_REQUIRED'
                    except Exception as error:
                        result['errors'].append({'path':str(path),'error':type(error).__name__})
            except PermissionError:
                root_state['status']='PERMISSION_REQUIRED'
            result['roots'].append(root_state)
        with self.store.connection() as db:
            db.execute('INSERT INTO font_scan_events(data) VALUES (?)',(json.dumps(result),))
        return result

    def _metadata(self, path, file_hash, index, origin):
        font = TTFont(str(path),fontNumber=index,lazy=True)
        try:
            names = font['name']
            def name(id):
                records = [r for r in names.names if r.nameID==id]
                # English metadata preferred for stable family matching; retain all names in font bytes.
                records.sort(key=lambda r: r.langID not in (0x409,0))
                for item in records:
                    try:
                        return item.toUnicode()
                    except Exception:
                        continue
                return ''
            cmap = font.getBestCmap() or {}
            os2 = font.get('OS/2')
            axes = [{'tag':a.axisTag,'min':a.minValue,'default':a.defaultValue,'max':a.maxValue}
                    for a in font['fvar'].axes] if 'fvar' in font else []
            classes = []
            if any(0x4e00<=c<=0x9fff for c in cmap): classes.append('CJK')
            if all(c in cmap for c in range(65,91)): classes.append('ENGLISH')
            if {'CJK','ENGLISH'}<=set(classes): classes.append('BOTH')
            if 'post' in font and font['post'].isFixedPitch: classes.append('MONOSPACE')
            if os2 and os2.panose.bFamilyType==2:
                classes.append('SANS' if os2.panose.bSerifStyle in (11,12,13) else 'SERIF' if 2<=os2.panose.bSerifStyle<=10 else 'UNKNOWN')
            elif os2 and os2.panose.bFamilyType==3: classes.append('HANDWRITING')
            else: classes.append('UNKNOWN')
            if axes: classes.append('VARIABLE')
            family = name(16) or name(1) or path.stem
            return FontRecord(font_id='FONT-'+digest([str(path),file_hash,index])[:20],
                family=family,subfamily=name(17) or name(2),full_name=name(4),postscript_name=name(6),
                source=origin,file_path=str(path),file_name=path.name,file_type=path.suffix[1:].upper(),
                file_hash=file_hash,face_index=index,version=name(5),weight=os2.usWeightClass if os2 else 400,
                style='italic' if os2 and os2.fsSelection&1 else 'normal',stretch=os2.usWidthClass if os2 else 5,
                variable=bool(axes),axes=axes,languages=[x for x in classes if x in ('CJK','ENGLISH')],
                classification=classes,preview_path='',preview_hash='')
        finally:
            font.close()

    def face(self, font_id):
        value = self.get(font_id)
        source = Path(value.file_path)
        if not source.is_file(): raise ValueError('FONT_MISSING')
        if sha(source)!=value.file_hash: raise ValueError('FONT_HASH_CHANGED')
        folder = self.cache/value.file_hash
        folder.mkdir(parents=True,exist_ok=True)
        # A TTC face is extracted once. Browser and renderer consume these exact same bytes.
        output = folder/f'face-{value.face_index}.otf'
        if not output.exists():
            font = TTFont(str(source),fontNumber=value.face_index)
            font.recalcTimestamp = False
            font.flavor = None
            temp = output.with_suffix('.tmp')
            font.save(str(temp))
            font.close()
            temp.replace(output)
        value.preview_path = str(output)
        value.preview_hash = sha(output)
        with self.store.connection() as db:
            db.execute('UPDATE fonts SET data=? WHERE id=?',(value.model_dump_json(),font_id))
        return value

    def profile(self, pid, payload):
        value = TypographyProfile.model_validate(payload)
        records = []
        ids = {r.font_id for r in value.roles.values()}
        if value.fallback_font_id: ids.add(value.fallback_font_id)
        for fid in sorted(ids):
            record = self.face(fid)
            records.append(record.model_dump())
        for role in value.roles.values():
            font = next(x for x in records if x['font_id']==role.font_id)
            axis = next((a for a in font['axes'] if a['tag']=='wght'),None)
            if axis and not axis['min']<=role.weight<=axis['max']:
                raise ValueError('FONT_WEIGHT_OUT_OF_RANGE')
            if not axis and role.weight!=font['weight']:
                raise ValueError('FONT_STATIC_WEIGHT_MISMATCH')
        profile = self.store.create_artifact(pid,'TYPOGRAPHY_PROFILE',value.model_dump(),role='TYPOGRAPHY')
        snapshot = self.store.create_artifact(pid,'PROJECT_FONT_SNAPSHOT',
            {'typography_profile_id':profile.artifact_id,'typography_profile_hash':profile.output_hash,
             'fonts':records,'policy':value.production_policy,'local_only':True},role='FONT_REGISTRY',
            dependencies=[self.store.dependency(profile.artifact_id)])
        return {**profile.model_dump(),'font_snapshot_artifact_id':snapshot.artifact_id}

    def check(self, pid, texts: list[tuple[str,str]]):
        snapshot = self.store.latest(pid,'PROJECT_FONT_SNAPSHOT')
        profile = self.store.latest(pid,'TYPOGRAPHY_PROFILE')
        if not snapshot or not profile:
            return [{'code':'FONT_MISSING','severity':'BLOCKER','owner':'TYPOGRAPHY','description':'Typography profile required'}]
        if not self.store.is_usable_input(snapshot['artifact_id']):
            return [{'code':'FONT_RENDER_MISMATCH','severity':'BLOCKER','owner':'TYPOGRAPHY','description':'Snapshot is stale'}]
        issues = []
        fonts = {x['font_id']:x for x in snapshot['payload']['fonts']}
        for fid,font in fonts.items():
            source,cache = Path(font['file_path']),Path(font['preview_path'])
            for code, broken in [('FONT_MISSING',not source.is_file() or not cache.is_file()),
                                 ('FONT_HASH_CHANGED',source.is_file() and sha(source)!=font['file_hash']),
                                 ('FONT_RENDER_MISMATCH',cache.is_file() and sha(cache)!=font['preview_hash'])]:
                if broken: issues.append({'code':code,'severity':'BLOCKER','owner':'TYPOGRAPHY','description':fid})
        for role,text in texts:
            selected = profile['payload']['roles'][role]['font_id']
            cache = Path(fonts[selected]['preview_path'])
            if not cache.is_file(): continue
            font = TTFont(str(cache),lazy=True)
            cmap = font.getBestCmap() or {}
            missing = [c for c in set(text) if not c.isspace() and ord(c) not in cmap]
            font.close()
            if missing:
                fallback = profile['payload'].get('fallback_font_id')
                allow = profile['payload']['production_policy']=='ALLOW_FALLBACK' and fallback in fonts
                covered = False
                if allow and Path(fonts[fallback]['preview_path']).is_file():
                    f = TTFont(fonts[fallback]['preview_path'],lazy=True)
                    covered = all(ord(c) in (f.getBestCmap() or {}) for c in missing)
                    f.close()
                issues.append({'code':'FONT_FALLBACK_ACTIVE' if covered else 'FONT_GLYPH_MISSING',
                    'severity':'WARNING' if covered else 'BLOCKER','owner':'TYPOGRAPHY',
                    'description':role+': '+''.join(sorted(missing))})
        return issues

    def render_dependencies(self, pid):
        snapshot = self.store.latest(pid,'PROJECT_FONT_SNAPSHOT')
        profile = self.store.latest(pid,'TYPOGRAPHY_PROFILE')
        if not snapshot or not profile: return None
        import copy
        from vnext.phase2.hardening.dependencies import Dependencies
        snapshot=copy.deepcopy(snapshot);relinks=Dependencies(self.store).relinks(pid)
        for font in snapshot['payload']['fonts']:
            if font['font_id'] in relinks:font['preview_path']=str(Dependencies(self.store).resolved(pid,font['font_id'],font['preview_path'],font['preview_hash']))
        return {'profile':profile,'snapshot':snapshot}
