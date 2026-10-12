import {translate, present, summaryHtml} from '/i18n.js';
import {monitorHtml, selectClip} from '/preview.js';

// The visual workbench edits Director-owned fields only. The preview EDT is derived.
export function initStoryboardWorkflow({api, app, project, refresh, esc, latest, act}) {
  const $ = selector => document.querySelector(selector);
  const t = key => translate(app, 'story.' + key);
  const pid = () => project().project_id;
  const option = (value, label, selected) => `<option value="${esc(value)}" ${selected ? 'selected' : ''}>${esc(label)}</option>`;
  const beatOrder = ir => ir.payload.scenes.flatMap(scene => scene.beat_ids.map(id => ({scene, beat: ir.payload.beats.find(b => b.beat_id === id)})));
  const scriptText = id => latest('SCRIPT')?.payload.segments.find(s => s.segment_id === id)?.text || '';
  const mediaOptions = () => (app.detail.media || []).filter(a => ['IMAGE', 'SCREENSHOT', 'VIDEO'].includes(a.type));
  const actionOptions = () => app.catalog.characters.find(x => x.character_id === project().character_pack)?.actions || [];
  const required = patternId => app.phase2State?.patterns.find(p => p.pattern_id === patternId)?.required_slots || [];
  const slots = ['media_asset_id', 'a', 'b', 'number', 'steps', 'points', 'actions'];
  const listSlots = new Set(['steps', 'points', 'actions']);
  const hasHumanEdtEdit = () => {
    const commands = app.detail.artifacts.filter(a => a.artifact_type === 'EDIT_COMMAND' && a.payload.target === 'EDT').map(a => a.payload);
    const generated = commands.findLastIndex(c => ['GENERATE_REVISION', 'GENERATE', 'GENERATE_PRESERVING_AUDIO'].includes(c.operation));
    return commands.slice(generated + 1).some(c => c.actor_type === 'HUMAN');
  };
  const semanticFor = {CHARACTER_EXPLAIN_KEYWORD: 'EXPLAIN', CHARACTER_REACTION_MEDIA: 'REACTION',
    TIMELINE_PROCESS: 'PROCESS', A_B_COMPARE: 'COMPARE', SCREEN_DETAIL: 'EVIDENCE',
    THREE_POINT_SUMMARY: 'SUMMARY', NUMBER_EMPHASIS: 'NUMBER', CHARACTER_ACTION_SEQUENCE: 'EXPLAIN'};

  function slotField(beat, field) {
    const value = beat.slots[field];
    const label = t('slot.' + field);
    if (field === 'media_asset_id') return `<label data-story-slot="${field}">${esc(label)}<select data-slot-value="${field}">${option('', t('chooseAsset'), !value)}${mediaOptions().map(a => option(a.asset_id, a.display_name || a.asset_id, a.asset_id === value)).join('')}</select></label>`;
    return `<label data-story-slot="${field}">${esc(label)}<input data-slot-value="${field}" value="${esc(Array.isArray(value) ? value.join('、') : value || '')}"></label>`;
  }
  function beatCard(scene, beat, patterns, actions) {
    const revision = latest('DIRECTOR_IR');
    return `<article class="story-beat" data-story-beat="${esc(beat.beat_id)}" data-expected-revision="${esc(revision.artifact_id)}">
      <header><strong>${esc(scene.scene_id)} / ${esc(beat.beat_id)}</strong><span>${esc(beat.timing_intent)}s · ${esc(beat.purpose)}</span></header>
      <p class="story-script">${esc(scriptText(beat.script_segment_id))}</p>
      <div class="story-edit-grid">
        <label>${esc(t('pattern'))}<select data-story-pattern>${patterns.map(p => option(p.pattern_id, present(app, p.pattern_id), p.pattern_id === beat.pattern_id)).join('')}</select></label>
        <label>${esc(t('action'))}<select data-story-action>${option('', t('automaticAction'), !beat.character_action_id)}${actions.map(a => option(a.id, a.label_zh || a.label || a.id, a.id === beat.character_action_id)).join('')}</select></label>
        <label>${esc(t('keyword'))}<input data-story-keyword value="${esc(beat.keyword)}"></label>
        ${slots.map(field => slotField(beat, field)).join('')}
      </div>
      <div class="row"><button data-story="save" data-beat="${esc(beat.beat_id)}">${esc(t('saveBeat'))}</button><button data-story="split" data-beat="${esc(beat.beat_id)}">${esc(t('splitBeat'))}</button><button data-story="jump" data-beat="${esc(beat.beat_id)}">${esc(t('previewBeat'))}</button></div>
    </article>`;
  }
  function updateSlotVisibility(card) {
    const used = new Set(required(card.querySelector('[data-story-pattern]').value));
    card.querySelectorAll('[data-story-slot]').forEach(field => { field.hidden = !used.has(field.dataset.storySlot); });
  }
  function view() {
    const ir = latest('DIRECTOR_IR'), edt = latest('EDT'), board = latest('STORYBOARD');
    const currentBoard = board?.current_status === 'READY' ? board : null;
    const gate = latest('STORYBOARD_GATE');
    const patterns = app.phase2State?.patterns || [];
    const actions = actionOptions();
    if (!ir) return `<div class="card"><h3>${esc(t('title'))}</h3><p>${esc(t('directorRequired'))}</p><button data-node="director">${esc(t('goDirector'))}</button></div>`;
    const voice = latest('VOICE');
    const usableFonts = app.fontOptions.filter(f => f.status === 'AVAILABLE' && f.classification.includes('CJK') && f.style === 'normal');
    const selectedFontId = latest('TYPOGRAPHY_PROFILE')?.payload?.roles?.BODY?.font_id;
    const preferred = usableFonts.find(f => f.font_id === selectedFontId) ||
      usableFonts.find(f => f.family === 'Heiti SC' && f.weight === 400) ||
      usableFonts.find(f => f.family === 'Hiragino Sans GB') ||
      usableFonts.find(f => f.weight === 400 && !f.family.startsWith('.')) ||
      usableFonts.find(f => !f.family.startsWith('.')) || usableFonts[0];
    const typography = `<details class="card" ${latest('TYPOGRAPHY_PROFILE')?'':'open'}><summary>${esc(t('typography'))}${selectedFontId?' · '+esc(preferred?.family||selectedFontId):''}</summary><p>${esc(t('typographyNotice'))}</p><div class="row"><select id="storyFont">${usableFonts.map(f => option(f.font_id, `${f.family} · ${f.subfamily} · ${f.weight}`, f.font_id === preferred?.font_id)).join('')}</select><button data-story="scanFonts">${esc(t('scanFonts'))}</button><button data-story="applyFont" ${preferred ? '' : 'disabled'}>${esc(t('applyFont'))}</button></div></details>`;
    return `${typography}<div class="card"><h3>${esc(t('title'))}</h3><p>${esc(t('sourceOfTruth'))}</p><div class="row"><strong>${esc(t('directorRevision'))} v${ir.revision}</strong><button data-story="undo" ${ir.revision < 2 ? 'disabled' : ''}>${esc(t('undo'))}</button><button data-story="refreshPreview" ${voice || !latest('TYPOGRAPHY_PROFILE') ? 'disabled' : ''}>${esc(t('refreshPreview'))}</button><button data-story="stills" ${!edt || edt.current_status !== 'READY' ? 'disabled' : ''}>${esc(t('formalStills'))}</button></div><p class="muted">${esc(voice ? t('voiceExists') : t('previewFirst'))}</p></div>
      ${edt ? monitorHtml(app, esc) : ''}
      <section class="story-scenes">${beatOrder(ir).map(({scene, beat}) => beatCard(scene, beat, patterns, actions)).join('')}</section>
      <div class="card"><h3>${esc(t('gate'))}</h3>${currentBoard ? `<p>${esc(t('stillsReady'))} · v${currentBoard.revision}</p><div class="story-contact-sheet">${currentBoard.payload.entries.map(e => `<article><strong>${esc(e.scene_id)} / ${esc(e.beat_id)} · ${esc(e.pattern_id)}</strong><div>${e.images.map((_, i) => `<figure><img src="/api/projects/${esc(pid())}/phase2/storyboard/${esc(currentBoard.artifact_id)}/${esc(e.beat_id)}/${i}/file" alt="${esc(e.beat_id)} ${i ? 'End' : 'Start'}"><figcaption>${i ? 'End' : 'Start'}</figcaption></figure>`).join('')}</div></article>`).join('')}</div><label>${esc(t('reviewer'))}<input id="storyReviewer"></label><label>${esc(t('comments'))}<input id="storyComments"></label><div class="row"><button data-story="approve">${esc(t('approve'))}</button><button data-story="reject">${esc(t('reject'))}</button></div>` : `<p>${esc(t('stillsRequired'))}</p>`}${summaryHtml(app, gate, esc)}</div>
      <details class="card"><summary>${esc(t('history'))}</summary>${app.detail.artifacts.filter(a => ['DIRECTOR_IR', 'STORYBOARD', 'STORYBOARD_GATE'].includes(a.artifact_type)).map(a => `<p>${esc(a.created_at)} · ${esc(a.artifact_type)} v${a.revision} · ${esc(a.current_status)}</p>`).join('')}</details>`;
  }
  function changes(card) {
    const patternId = card.querySelector('[data-story-pattern]').value;
    const original = latest('DIRECTOR_IR').payload.beats.find(b => b.beat_id === card.dataset.storyBeat);
    const patternChanged = original.pattern_id !== patternId;
    const chosen = patternChanged ? {} : {...original.slots};
    for (const field of required(patternId)) {
      if (field === 'keyword') continue;
      const raw = card.querySelector(`[data-slot-value="${field}"]`).value.trim();
      chosen[field] = listSlots.has(field) ? raw.split(/[、,，\n]/).map(x => x.trim()).filter(Boolean) : raw;
    }
    const keyword = card.querySelector('[data-story-keyword]').value.trim();
    if (required(patternId).includes('keyword')) chosen.keyword = keyword;
    return {pattern_id: patternId, semantic_pattern: semanticFor[patternId],
      template_id: patternChanged ? null : original.template_id, keyword,
      character_action_id: card.querySelector('[data-story-action]').value || null, slots: chosen};
  }
  document.addEventListener('change', event => {
    if (event.target.matches('[data-story-pattern]')) updateSlotVisibility(event.target.closest('[data-story-beat]'));
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-story]');
    if (!button || !project()) return;
    const operation = button.dataset.story;
    if (operation === 'jump') {
      const clip = latest('EDT')?.payload.clips.find(c => c.beat_id === button.dataset.beat && c.track !== 'SUBTITLE');
      if (clip) selectClip(app, clip.clip_id, () => {});
      return;
    }
    const discardPreviewEdits = operation === 'refreshPreview' && hasHumanEdtEdit();
    if (discardPreviewEdits && !window.confirm(t('discardConfirm'))) return;
    act(async () => {
      button.disabled = true;
      try {
        const ir = latest('DIRECTOR_IR'), edt = latest('EDT');
        if (operation === 'scanFonts') {
          await api('/api/fonts/rescan', 'POST', {});
          app.fontOptions = await api('/api/fonts');
        } else if (operation === 'applyFont') {
          const font = app.fontOptions.find(f => f.font_id === $('#storyFont').value);
          if (!font) throw Error(t('scanFonts'));
          const words = [...(latest('SCRIPT')?.payload.segments||[]).map(s=>s.text),...(latest('DIRECTOR_IR')?.payload.beats||[]).map(b=>b.keyword||'')].join('');
          const coverage = await api(`/api/fonts/${font.font_id}/coverage?text=${encodeURIComponent(words)}`);
          if (coverage.missing.length) throw Error(`FONT_GLYPH_MISSING: ${coverage.missing.slice(0,12).join('')}`);
          const sizes = {TITLE: 64, BODY: 43, SUBTITLE: 44, KEYWORD: 68, NUMBER: 74, LABEL: 37, CTA: 57, UI: 30};
          const roles = Object.fromEntries(Object.entries(sizes).map(([role, size]) => [role, {font_id: font.font_id, weight: font.weight, size}]));
          const profile = {profile_id: 'P0_GUI_FONT_V1', version: '1', roles,
            presentation: project().character_pack ? 'XIAOY_EXPLAINER' : 'STANDARD'};
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'TYPOGRAPHY_PROFILE', operation: 'SET_TYPOGRAPHY_PROFILE', arguments: {profile}, expected_revision: latest('TYPOGRAPHY_PROFILE')?.artifact_id || null, reason: 'GUI typography selection'});
        } else if (operation === 'save') {
          const card = button.closest('[data-story-beat]');
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'DIRECTOR_IR', operation: 'SET_BEAT', arguments: {beat_id: button.dataset.beat, changes: changes(card)}, expected_revision: card.dataset.expectedRevision, reason: 'GUI beat edit'});
        } else if (operation === 'split') {
          const card = button.closest('[data-story-beat]');
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'DIRECTOR_IR', operation: 'SPLIT_BEAT', arguments: {beat_id: button.dataset.beat}, expected_revision: card.dataset.expectedRevision, reason: 'GUI split one segment into two visual beats'});
        } else if (operation === 'undo') {
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'DIRECTOR_IR', operation: 'UNDO', arguments: {}, expected_revision: ir.artifact_id, reason: 'GUI director undo'});
        } else if (operation === 'refreshPreview') {
          if (latest('VOICE')) throw Error(t('voiceExists'));
          await api(`/api/projects/${pid()}/phase2/commands`, 'POST', {target: 'EDT', operation: 'GENERATE', arguments: {discard_human_edits: discardPreviewEdits}, expected_revision: edt?.artifact_id || null, reason: 'GUI provisional preview'});
        } else if (operation === 'stills') {
          await api(`/api/projects/${pid()}/phase2/storyboard-job?expected_director_revision=${encodeURIComponent(ir.artifact_id)}&expected_edt_revision=${encodeURIComponent(edt.artifact_id)}`, 'POST', {});
        } else if (operation === 'approve' || operation === 'reject') {
          const reviewer = $('#storyReviewer')?.value.trim(), comments = $('#storyComments')?.value.trim() || '';
          await api(`/api/projects/${pid()}/phase2/storyboard/gate`, 'POST', {artifact_id: latest('STORYBOARD').artifact_id, decision: operation === 'approve' ? 'APPROVE' : 'REJECT', reviewer, comments});
        }
        await refresh();
      } finally { button.disabled = false; }
    });
  });
  return {view, updateSlotVisibility};
}
