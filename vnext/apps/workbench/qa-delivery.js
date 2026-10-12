import {translate,present} from '/i18n.js';

export function initQADelivery({api,app,project,refresh,esc,latest,act}) {
  const $ = selector => document.querySelector(selector);
  const t = key => translate(app,'p0qa.'+key);
  const pid = () => project().project_id;
  const ready = artifact => artifact?.current_status === 'READY';
  const issues = artifact => artifact?.payload?.issues || [];
  const issueList = artifact => issues(artifact).length
    ? `<ul>${issues(artifact).map(item => `<li><strong>${esc(item.code)}</strong> · ${esc(present(app,item.severity))} · ${esc(present(app,item.owner))} · ${esc(item.description || '')}</li>`).join('')}</ul>`
    : `<p>${esc(t('noIssues'))}</p>`;

  function view() {
    const mechanical=latest('MECHANICAL_QA'), visual=latest('VIDEO_QA'), pack=latest('REVIEW_PACK'), gate=latest('REVIEW_GATE');
    const render=latest('RENDER'), hasVideo=ready(render)&&render.payload.media_type==='video/mp4';
    const risks=ready(pack)?pack.payload.risks||[]:[];
    const provider=visual?.provider||visual?.worker||'—';
    const scope=!visual?t('awaiting'):visual.payload.mock?t('mockScope'):t('visualScope');
    return `<div class="card"><h3>${esc(t('qaTitle'))}</h3><p>${esc(t('qaSequence'))}</p><div class="row">
      <button data-qa-action="mechanical" ${hasVideo?'':'disabled'}>${esc(t('runMechanical'))}</button>
      <button data-qa-action="visual" ${ready(mechanical)&&mechanical.payload.verdict!=='FAIL'?'':'disabled'}>${esc(t('runVisual'))}</button>
      <button data-qa-action="review" ${ready(mechanical)&&ready(visual)&&mechanical.payload.verdict!=='FAIL'&&visual.payload.verdict!=='FAIL'?'':'disabled'}>${esc(t('buildReview'))}</button>
    </div></div>
    <div class="p2qa"><article class="card"><h3>${esc(t('mechanical'))}</h3><p>${esc(t('verdict'))}: ${esc(present(app,mechanical?.payload?.verdict||'—'))}</p>${mechanical?issueList(mechanical):`<p>${esc(t('awaiting'))}</p>`}</article>
    <article class="card"><h3>${esc(t('visual'))}</h3><p>${esc(t('provider'))}: ${esc(provider)} · ${esc(t('scope'))}: ${esc(scope)}</p><p>${esc(t('verdict'))}: ${esc(present(app,visual?.payload?.verdict||'—'))}</p>${visual?issueList(visual):`<p>${esc(t('awaiting'))}</p>`}</article></div>
    <div class="card"><h3>${esc(t('h3Title'))}</h3><p>${esc(t('h3NotH4'))}</p>${ready(pack)
      ? `<p>${esc(t('reviewVersion'))}: v${pack.revision} · ${esc(pack.artifact_id)}</p><p>${esc(t('riskCount'))}: ${risks.length}</p>
        ${risks.map((risk,index)=>`<label class="qa-risk"><input type="checkbox" data-qa-risk="${esc(risk.code)}"><span>${index+1}. ${esc(risk.code)} · ${esc(risk.description||'')} · ${esc(present(app,risk.severity||'WARNING'))}</span></label>`).join('')}
        <label>${esc(t('reviewer'))}<input id="h3Reviewer" autocomplete="name"></label>
        <label>${esc(t('decision'))}<select id="h3Decision"><option value="APPROVE">${esc(t('approve'))}</option><option value="APPROVE_WITH_RISK">${esc(t('approveRisk'))}</option><option value="REJECT">${esc(t('reject'))}</option></select></label>
        <label>${esc(t('comments'))}<textarea id="h3Comments" rows="3"></textarea></label>
        <button data-qa-action="h3">${esc(t('submitH3'))}</button>`
      : `<p>${esc(t('reviewRequired'))}</p>`}
      ${gate?`<p>${esc(t('h3Status'))}: ${esc(present(app,gate.payload.decision))} · ${esc(gate.payload.reviewer)} · ${esc(t('publishAuthorization'))}: ${gate.payload.publish_authorized?'true':'false'}</p>`:''}
    </div>`;
  }

  function deliverView() {
    const render=latest('RENDER'),gate=latest('REVIEW_GATE'),exported=latest('EXPORT');
    const h3=ready(gate)&&['APPROVE','APPROVE_WITH_RISK'].includes(gate.payload.decision);
    const mp4=h3&&ready(render)&&render.payload.media_type==='video/mp4';
    const bundle=h3&&ready(exported);
    return `<div class="card"><h3>${esc(t('deliverTitle'))}</h3><p>${esc(t('h3NotH4'))}</p>
      <p>${esc(t('h3Status'))}: ${h3?esc(present(app,gate.payload.decision)):esc(t('h3Pending'))}</p>
      ${mp4?`<a class="button" href="/api/projects/${esc(pid())}/render/${esc(render.artifact_id)}/download" download>${esc(t('downloadMp4'))}</a>`:`<p>${esc(t('mp4NotReady'))}</p>`}
      <div class="row"><button data-qa-action="export" ${h3?'':'disabled'}>${esc(t('exportJianying'))}</button>
      ${bundle?`<a class="button" href="/api/projects/${esc(pid())}/jianying/export/${esc(exported.artifact_id)}/download" download>${esc(t('downloadJianying'))}</a>`:''}</div>
      <p>${bundle?`${esc(t('exportReady'))}: ${esc(exported.artifact_id)}`:esc(t('exportNotReady'))}</p>
      ${bundle?`<p>${esc(t('exportLocation'))}: ${esc(exported.payload.path)}</p><p>${esc(t('exportContents'))}: transfer manifest, subtitles, native draft, report.</p><p class="warn">${esc(exported.payload.limitation||'')}</p>`:''}
    </div>`;
  }

  document.addEventListener('click', event => {
    const button=event.target.closest('[data-qa-action]');
    if(!button||!project())return;
    const action=button.dataset.qaAction;
    act(async()=>{
      button.disabled=true;
      try {
        if(action==='mechanical')await api(`/api/projects/${pid()}/phase2/mechanical-qa`,'POST',{});
        if(action==='visual')await app.productionUX.videoQA();
        if(action==='review')await api(`/api/projects/${pid()}/phase2/review`,'POST',{});
        if(action==='export')await api(`/api/projects/${pid()}/jianying/export`,'POST',{});
        if(action==='h3'){
          const pack=latest('REVIEW_PACK'),decision=$('#h3Decision').value;
          const risks=pack?.payload?.risks||[];
          const checked=[...document.querySelectorAll('[data-qa-risk]:checked')];
          if(decision==='APPROVE_WITH_RISK'&&checked.length!==risks.length)throw Error(t('ackAllRisks'));
          if(decision==='APPROVE'&&risks.length)throw Error(t('chooseRiskDecision'));
          await api(`/api/projects/${pid()}/phase2/review/gate`,'POST',{
            artifact_id:pack.artifact_id,decision,reviewer:$('#h3Reviewer').value,
            comments:$('#h3Comments').value,accepted_risks:checked.map(node=>node.dataset.qaRisk)});
        }
        await refresh();
      } finally {button.disabled=false}
    });
  });
  return {view,deliverView};
}
