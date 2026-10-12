// Read-only projection. All status comes from persisted project/artifact truth.
export function workflowProjection(detail) {
  if (!detail) return null;
  const project = detail.project;
  const artifacts = detail.artifacts || [];
  const latest = kind => artifacts.filter(a => a.artifact_type === kind).at(-1);
  const ready = kind => latest(kind)?.current_status === 'READY';
  const sourceArtifact = artifacts.filter(a => a.artifact_type.startsWith('SOURCE_')).at(-1);
  const source = artifacts.some(a => a.artifact_type.startsWith('SOURCE_') && a.current_status === 'READY');
  const h2 = project.h2_script_artifact_id && project.h2_script_artifact_id === latest('SCRIPT')?.artifact_id && ready('AUDIT');
  const board = ready('STORYBOARD_GATE') && latest('STORYBOARD_GATE')?.payload?.all_beats_approved === true;
  const voice = ready('VOICE') && ready('AUDIO_TIMING_MAP');
  const edt = latest('EDT');
  const finalEdt = voice && ready('EDT') && edt.dependencies.some(d => d.artifact_id === latest('VOICE').artifact_id) &&
    edt.payload.clips.some(clip => clip.track === 'VOICE');
  const render = ready('RENDER') && latest('RENDER')?.payload?.media_type === 'video/mp4';
  const qa = ready('MECHANICAL_QA') && ready('VIDEO_QA');
  const h3 = ready('REVIEW_GATE') && ['APPROVE','APPROVE_WITH_RISK'].includes(latest('REVIEW_GATE')?.payload?.decision);
  const steps = [
    ['research', source, 'source', sourceArtifact],
    ['research', ready('FACT_PACK'), 'fact', latest('FACT_PACK')],
    ['script', ready('SCRIPT'), 'script', latest('SCRIPT')],
    ['audit', !!h2, 'h2', latest('AUDIT')],
    ['director', ready('DIRECTOR_IR'), 'director', latest('DIRECTOR_IR')],
    ['visual', board, 'storyboard', latest('STORYBOARD_GATE')],
    ['voice', voice, 'voice', latest('VOICE')],
    ['timeline', finalEdt, 'timeline', latest('EDT')],
    ['render', render, 'render', latest('RENDER')],
    ['videoqa', qa, 'qa', latest('VIDEO_QA')],
    ['videoqa', h3, 'h3', latest('REVIEW_GATE')]
  ];
  const current = steps.find(([,done]) => !done) || ['publish',false,'deliver',latest('RENDER')];
  const coverage = latest('CLAIM_COVERAGE_REPORT'), decision = latest('CLAIM_COVERAGE_DECISION');
  const riskArtifacts = [coverage,latest('AUDIT'),latest('MECHANICAL_QA'),latest('VIDEO_QA'),latest('REVIEW_PACK')]
    .filter(a => a?.current_status === 'READY');
  const candidatesReviewed = decision?.current_status === 'READY' && decision.payload?.report_id === coverage?.artifact_id &&
    decision.payload.decisions?.every(item => item.decision === 'NON_CLAIM');
  const riskCount = riskArtifacts.reduce((count,a) => count + (a.payload?.risks?.length || 0) +
    (a.payload?.findings?.length || 0) + (a.payload?.issues?.length || 0) +
    (a === coverage && !candidatesReviewed ? a.payload?.candidates?.length || 0 : 0),0);
  const nodeStatuses = {};
  for (const [node,done] of steps) nodeStatuses[node] = nodeStatuses[node] === false ? false : !!done;
  return {node:current[0], stage:current[2], artifact:current[3], gate:latest('REVIEW_GATE')?.current_status === 'READY' ? latest('REVIEW_GATE') :
    latest('STORYBOARD_GATE')?.current_status === 'READY' ? latest('STORYBOARD_GATE') : latest('H2_GATE'),
    riskCount:riskArtifacts.length ? riskCount : null, historyCount:artifacts.length, nodeStatuses};
}
