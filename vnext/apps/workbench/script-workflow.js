// Strict-script editing stays on the existing CommandBus and evidence contract.
// The UI never infers that a rewritten factual sentence is supported by an old Fact.
export function strictScriptView({script, factPack, audit, coverage, versions, t, esc}) {
  const payload = script.payload;
  const supported = (factPack?.payload?.facts || []).filter(f => f.support_status === 'SUPPORTED');
  const factOptions = ids => supported.map(f => `<option value="${esc(f.fact_id)}" ${ids.includes(f.fact_id) ? 'selected' : ''}>${esc(f.fact_id)} · ${esc(f.statement)}</option>`).join('');
  const types = ['FACTUAL', 'NUMERIC', 'ATTRIBUTION', 'PREDICTION', 'OPINION', 'NON_CLAIM'];
  const claimRow = claim => `<div class="claim-row" data-claim-id="${esc(claim.claim_id)}" data-segment-id="${esc(claim.segment_id)}">
    <label>${esc(t('claimText'))}<input data-claim-text value="${esc(claim.claim_text)}"></label>
    <label>${esc(t('claimType'))}<select data-claim-type>${types.map(type => `<option value="${type}" ${claim.claim_type === type ? 'selected' : ''}>${esc(t('claimType' + type))}</option>`).join('')}</select></label>
    <label>${esc(t('supportedFacts'))}<select data-claim-facts multiple size="3">${factOptions(claim.fact_ids || [])}</select></label>
    <button type="button" data-script-remove-claim>${esc(t('removeClaim'))}</button>
  </div>`;
  const segments = payload.segments.map(segment => {
    const claims = payload.claim_units.filter(c => c.segment_id === segment.segment_id);
    return `<article class="script-segment" data-script-segment="${esc(segment.segment_id)}">
      <h4>${esc(segment.segment_id)}</h4><textarea data-segment-text>${esc(segment.text)}</textarea>
      <details><summary>${esc(t('claimFactBinding'))} · ${claims.length}</summary>
        <p class="muted">${esc(t('claimBindingHelp'))}</p><div data-claim-list>${claims.map(claimRow).join('')}</div>
        <button type="button" data-script-add-claim>${esc(t('addClaim'))}</button>
      </details>
    </article>`;
  }).join('');
  const previous = versions.at(-2);
  const canH2 = script.current_status === 'READY' && audit?.current_status === 'READY' &&
    coverage?.current_status === 'READY' && coverage.payload?.script_artifact_id === script.artifact_id;
  return `<div class="card"><h3>${esc(t('scriptText'))} · v${script.revision}</h3>
    <p class="muted">${esc(t('strictScriptEditorHelp'))}</p>${segments}
    <div class="row"><button class="primary" data-action="saveScript">${esc(t('save'))}</button>
      <button data-action="runAudit">${esc(t('runAudit'))}</button>
      <button data-action="approveH2" ${canH2 ? '' : 'disabled'}>${esc(t('approveH2'))}</button></div>
    ${previous ? `<details><summary>${esc(t('versionCompare'))} · v${previous.revision} → v${script.revision}</summary><div class="script-compare"><pre>${esc(previous.payload.text)}</pre><pre>${esc(payload.text)}</pre></div></details>` : ''}
    <details><summary>${esc(t('factEvidenceList'))}</summary>${supported.map(f => `<p>${esc(f.fact_id)} · ${esc(f.statement)}<small>${esc((f.evidence_ids || []).join(', '))}</small></p>`).join('')}</details>
  </div>`;
}

export function addClaimRow(segment, facts, t, esc) {
  const id = 'CU-' + crypto.randomUUID().replaceAll('-', '').slice(0, 12);
  const options = (facts?.payload?.facts || []).filter(f => f.support_status === 'SUPPORTED')
    .map(f => `<option value="${esc(f.fact_id)}">${esc(f.fact_id)} · ${esc(f.statement)}</option>`).join('');
  const row = document.createElement('div');
  row.className = 'claim-row';
  row.dataset.claimId = id;
  row.dataset.segmentId = segment.dataset.scriptSegment;
  row.innerHTML = `<label>${esc(t('claimText'))}<input data-claim-text></label>
    <label>${esc(t('claimType'))}<select data-claim-type><option value="FACTUAL">${esc(t('claimTypeFACTUAL'))}</option><option value="NUMERIC">${esc(t('claimTypeNUMERIC'))}</option><option value="ATTRIBUTION">${esc(t('claimTypeATTRIBUTION'))}</option><option value="PREDICTION">${esc(t('claimTypePREDICTION'))}</option><option value="OPINION">${esc(t('claimTypeOPINION'))}</option><option value="NON_CLAIM">${esc(t('claimTypeNON_CLAIM'))}</option></select></label>
    <label>${esc(t('supportedFacts'))}<select data-claim-facts multiple size="3">${options}</select></label>
    <button type="button" data-script-remove-claim>${esc(t('removeClaim'))}</button>`;
  segment.querySelector('[data-claim-list]').append(row);
  row.querySelector('[data-claim-text]').focus();
}

export function collectStrictScript(script, root, t) {
  const oldSegments = script.payload.segments;
  const rows = [...root.querySelectorAll('[data-script-segment]')];
  if (rows.length !== oldSegments.length) throw new Error(t('scriptSegmentsChanged'));
  const segments = [], claim_units = [];
  for (const [index, row] of rows.entries()) {
    const old = oldSegments[index], text = row.querySelector('[data-segment-text]').value.trim();
    if (!text) throw new Error(`${t('scriptSegmentEmpty')}: ${old.segment_id}`);
    const claims = [...row.querySelectorAll('[data-claim-id]')];
    for (const element of claims) {
      const claimText = element.querySelector('[data-claim-text]').value.trim();
      const type = element.querySelector('[data-claim-type]').value;
      const ids = [...element.querySelector('[data-claim-facts]').selectedOptions].map(option => option.value);
      const start = text.indexOf(claimText);
      if (!claimText || start < 0 || text.indexOf(claimText, start + 1) !== -1)
        throw new Error(`${t('claimSpanNotUnique')}: ${element.dataset.claimId}`);
      const factual = ['FACTUAL', 'NUMERIC', 'ATTRIBUTION'].includes(type);
      if (factual && !ids.length) throw new Error(`${t('claimFactRequired')}: ${element.dataset.claimId}`);
      if (['OPINION', 'NON_CLAIM'].includes(type) && ids.length)
        throw new Error(`${t('nonFactualFactForbidden')}: ${element.dataset.claimId}`);
      claim_units.push({claim_id:element.dataset.claimId, segment_id:old.segment_id,
        text_span:{start,end:start + claimText.length},claim_text:claimText,claim_type:type,fact_ids:ids,
        support_status:factual ? 'SUPPORTED' : type === 'PREDICTION' ? (ids.length ? 'PARTIAL' : 'UNSUPPORTED') : 'NOT_REQUIRED',
        review_status:'PENDING',review_reason:''});
    }
    const segmentClaims = claim_units.filter(claim => claim.segment_id === old.segment_id);
    const factualClaims = segmentClaims.filter(claim => ['FACTUAL','NUMERIC','ATTRIBUTION'].includes(claim.claim_type));
    segments.push({segment_id:old.segment_id,text,claim:factualClaims.length > 0,
      fact_ids:[...new Set(factualClaims.flatMap(claim => claim.fact_ids))]});
  }
  if (!claim_units.length) throw new Error(t('claimRequired'));
  return {contract_version:2,text:segments.map(segment => segment.text).join('\n'),segments,claim_units,
    semantic_status:'AUDIT_REQUIRED',semantic_diff:{source:'GUI_STRICT_SCRIPT_EDIT'},parent_script_artifact_id:script.artifact_id};
}
