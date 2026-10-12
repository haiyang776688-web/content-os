import {translate} from '/i18n.js';

const BY_NODE = {voice: ['P0_VOICE'], visual: ['P0_STORYBOARD'],
  render: ['P0_RENDER_VIDEO', 'P0_RENDER_STILL'], videoqa: ['P0_VIDEO_QA']};

export function activeLocalJob(detail) {
  return (detail?.jobs || []).some(j => j.kind.startsWith('P0_') && j.state === 'RUNNING');
}

export function jobStatusHtml(app, node, esc) {
  const t = key => translate(app, 'p0job.' + key);
  const kinds = BY_NODE[node] || [];
  const job = (app.detail?.jobs || []).find(j => kinds.includes(j.kind));
  if (!job) return '';
  const elapsed = job.started_at ? Math.max(0, Math.floor((Date.parse(job.finished_at || new Date().toISOString()) - Date.parse(job.started_at)) / 1000)) : 0;
  const clock = `${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`;
  const label = t(job.kind) || job.kind;
  const status = t(job.state) || job.state;
  return `<section class="card" data-local-job aria-label="${esc(t('title'))}"><h3>${esc(t('title'))}</h3><p>${esc(label)} · ${esc(status)} · ${esc(job.job_id)}</p>
    <p>${esc(t('stage'))}: ${esc(job.stage || '—')} · ${esc(t('elapsed'))} ${esc(clock)}</p>
    ${job.error ? `<p class="warn">${esc(job.error)}</p>` : ''}
    ${job.state === 'FAILED' ? `<p>${esc(t('retry'))}</p>` : ''}
    ${job.state === 'STALE' ? `<p class="warn">${esc(t('stale'))}</p>` : ''}</section>`;
}
