// Read-only testable projection; artifact dependencies remain the source of truth.
export function finalEditableEdt(detail) {
  const artifacts = detail?.artifacts || [];
  const latest = kind => artifacts.filter(a => a.artifact_type === kind).at(-1);
  const edt = latest('EDT'), voice = latest('VOICE'), timing = latest('AUDIO_TIMING_MAP');
  if (!edt || !voice || !timing || [edt, voice, timing].some(a => a.current_status !== 'READY')) return false;
  if (detail.project.timeline_artifact_id !== edt.artifact_id) return false;
  const refs = new Set(edt.dependencies.map(d => d.artifact_id));
  return refs.has(voice.artifact_id) && refs.has(timing.artifact_id) &&
    edt.payload.clips.some(c => c.track === 'VOICE' && c.asset_id === voice.payload.media_asset_id);
}
