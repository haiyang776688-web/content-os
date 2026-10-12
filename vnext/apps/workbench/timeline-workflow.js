import {translate, present} from '/i18n.js';
import {monitorHtml, selectClip} from '/preview.js';
import {finalEditableEdt} from '/timeline-state.js';

const VISUAL_TRACKS = new Set(['VIDEO', 'MEDIA', 'CHARACTER', 'ELEMENT', 'TEXT']);

export function initTimelineWorkflow({api, app, project, refresh, esc, latest, act}) {
  const $ = selector => document.querySelector(selector);
  const t = key => translate(app, 'p0timeline.' + key);
  const pid = () => project().project_id;
  const option = (value, label, selected) => `<option value="${esc(value)}" ${selected ? 'selected' : ''}>${esc(label)}</option>`;
  const visualClips = () => (latest('EDT')?.payload.clips || []).filter(c => VISUAL_TRACKS.has(c.track));
  const currentClip = () => visualClips().find(c => c.clip_id === ($('#p0Clip')?.value || app.selectedClip)) || visualClips()[0];
  const humanEdits = () => {
    const commands = app.detail.artifacts.filter(a => a.artifact_type === 'EDIT_COMMAND' && a.payload.target === 'EDT').map(a => a.payload);
    const generated = commands.findLastIndex(c => ['GENERATE_REVISION', 'GENERATE', 'GENERATE_PRESERVING_AUDIO'].includes(c.operation));
    return commands.slice(generated + 1).some(c => c.actor_type === 'HUMAN');
  };
  function view() {
    const edt = latest('EDT'), voice = latest('VOICE'), timing = latest('AUDIO_TIMING_MAP');
    const final = finalEditableEdt(app.detail);
    const clips = visualClips(), selected = clips.find(c => c.clip_id === app.selectedClip) || clips[0];
    const scenes = [...new Set(clips.map(c => c.scene_id).filter(Boolean))];
    const beatIds = [...new Set(clips.map(c => c.beat_id).filter(Boolean))];
    const media = (app.detail.media || []).filter(a => ['VIDEO', 'IMAGE', 'SCREENSHOT'].includes(a.type));
    const revision = edt ? `v${edt.revision} · ${present(app, edt.current_status)}` : '—';
    return `<div class="card"><h3>${esc(t('title'))}</h3><p>${esc(final ? t('finalReady') : t('provisional'))}</p><div class="row"><strong>${esc(t('revision'))}: ${esc(revision)}</strong>${!final ? `<button data-p0-timeline="build" ${!voice || !timing || timing.current_status !== 'READY' ? 'disabled' : ''}>${esc(t('buildFinal'))}</button>` : `<button data-p0-timeline="undo" ${edt.revision < 2 ? 'disabled' : ''}>${esc(t('undo'))}</button>`}</div>${!final ? `<p class="warn">${esc(!voice ? t('needVoice') : !timing ? t('needTiming') : t('buildRequired'))}</p>` : `<p class="muted">${esc(t('audioLocked'))}</p>`}</div>
      ${edt ? monitorHtml(app, esc) : ''}
      ${final ? `<div class="card"><h3>${esc(t('navigate'))}</h3><div class="row">${scenes.map(id => `<button data-p0-timeline="jumpScene" data-scene="${esc(id)}">${esc(id)}</button>`).join('')}</div><div class="row">${beatIds.map(id => `<button data-p0-timeline="jumpBeat" data-beat="${esc(id)}">${esc(id)}</button>`).join('')}</div></div>
      <div class="card"><h3>${esc(t('selectedVisual'))}</h3><label>${esc(t('element'))}<select id="p0Clip">${clips.map(c => option(c.clip_id, `${c.scene_id || '—'} / ${c.beat_id || '—'} · ${present(app, c.track)} · ${c.metadata?.text || c.asset_id || c.clip_id}`, c.clip_id === selected?.clip_id)).join('')}</select></label><div class="row"><label>X <input id="p0X" type="number" min="0" max="1" step="0.01" value="${selected?.position?.x ?? 0.5}"></label><label>Y <input id="p0Y" type="number" min="0" max="1" step="0.01" value="${selected?.position?.y ?? 0.5}"></label><label>${esc(t('scale'))} <input id="p0Scale" type="number" min="0.1" max="3" step="0.05" value="${selected?.scale ?? 1}"></label><label>${esc(t('opacity'))} <input id="p0Opacity" type="number" min="0" max="1" step="0.05" value="${selected?.opacity ?? 1}"></label><button data-p0-timeline="transform" ${!selected ? 'disabled' : ''}>${esc(t('applyVisual'))}</button></div><div class="row"><select id="p0Asset">${option('', t('chooseAsset'), true)}${media.map(a => option(a.asset_id, a.display_name || a.asset_id, false)).join('')}</select><button data-p0-timeline="replace" ${!selected || !['MEDIA', 'VIDEO'].includes(selected.track) ? 'disabled' : ''}>${esc(t('replaceAsset'))}</button></div><p class="muted">${esc(t('textPolicy'))}</p></div>` : ''}
      <details class="card"><summary>${esc(t('history'))}</summary>${app.detail.artifacts.filter(a => a.artifact_type === 'EDT').map(a => `<p>${esc(a.created_at)} · v${a.revision} · ${esc(a.current_status)} · ${esc(a.artifact_id)}</p>`).join('')}</details>`;
  }
  function syncClipFields() {
    const clip = currentClip();
    if (!clip) return;
    app.selectedClip = clip.clip_id;
    for (const [id, value] of [['p0X', clip.position?.x ?? .5], ['p0Y', clip.position?.y ?? .5],
      ['p0Scale', clip.scale ?? 1], ['p0Opacity', clip.opacity ?? 1]]) if ($(`#${id}`)) $(`#${id}`).value = value;
    const replacement = document.querySelector('[data-p0-timeline="replace"]');
    if (replacement) replacement.disabled = !['MEDIA', 'VIDEO'].includes(clip.track);
  }
  document.addEventListener('change', event => {
    if (event.target.id === 'p0Clip') {
      syncClipFields();
      selectClip(app, event.target.value, () => {});
    }
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-p0-timeline]');
    if (!button || !project()) return;
    const action = button.dataset.p0Timeline;
    if (action === 'jumpScene' || action === 'jumpBeat') {
      const clip = visualClips().find(c => action === 'jumpScene' ? c.scene_id === button.dataset.scene : c.beat_id === button.dataset.beat);
      if (clip) {
        $('#p0Clip').value = clip.clip_id;
        syncClipFields();
        selectClip(app, clip.clip_id, () => {});
      }
      return;
    }
    const discard = action === 'build' && humanEdits();
    if (discard && !window.confirm(t('discardConfirm'))) return;
    act(async () => {
      button.disabled = true;
      try {
        const edt = latest('EDT');
        if (action === 'build') {
          if (!latest('AUDIO_TIMING_MAP') || !latest('VOICE')) throw Error(t('needTiming'));
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'EDT', operation: 'GENERATE',
            arguments: {discard_human_edits: discard}, expected_revision: edt?.artifact_id || null, reason: 'GUI final editable EDT'});
        } else if (action === 'undo') {
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'EDT', operation: 'UNDO',
            arguments: {}, expected_revision: edt.artifact_id, reason: 'GUI timeline undo'});
        } else if (action === 'transform') {
          const clip = currentClip();
          const x = Number($('#p0X').value), y = Number($('#p0Y').value), scale = Number($('#p0Scale').value), opacity = Number($('#p0Opacity').value);
          if (![x, y, scale, opacity].every(Number.isFinite) || x < 0 || x > 1 || y < 0 || y > 1 || scale <= 0 || scale > 3 || opacity < 0 || opacity > 1) throw Error(t('invalidVisual'));
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'EDT', operation: 'TRANSFORM',
            arguments: {clip_id: clip.clip_id, position: {x, y}, scale, opacity}, expected_revision: edt.artifact_id, reason: 'GUI visual transform'});
        } else if (action === 'replace') {
          const clip = currentClip(), assetId = $('#p0Asset').value;
          if (!clip || !['MEDIA', 'VIDEO'].includes(clip.track) || !assetId) throw Error(t('chooseAsset'));
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'EDT', operation: 'REPLACE',
            arguments: {clip_id: clip.clip_id, asset_id: assetId}, expected_revision: edt.artifact_id, reason: 'GUI visual asset replacement'});
        }
        await refresh();
      } finally {button.disabled = false;}
    });
  });
  return {view};
}
