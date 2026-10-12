import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Character, Crop, ease, INK, Label, RED, YELLOW} from '../vgb001/shared';
import {Chrome, EvidenceCamera, HumanReview, Reaction, ShortCallout, SourceFactRelation, Underline, UI_DARK} from './shared';

export const F2: React.FC = () => {
  const t = useCurrentFrame() / 30;
  if (t < 2.91) {
    const handoff = ease(t, .72, 1.45);
    return (
      <AbsoluteFill style={{background: '#fff'}}>
        <Chrome section="01 · RESEARCH" light />
        <Character name="point" style={{left: 75 - 700 * handoff, top: 220, width: 550, height: 650}} />
        <Crop image="research" rect={[245, 493, 430, 205]} width={1040 + 710 * handoff} style={{left: 720 - 620 * handoff, top: 270 - 80 * handoff, boxShadow: '0 22px 55px #10131925'}} />
        <Underline left={735 - 570 * handoff} top={625 - 55 * handoff} width={320 + 150 * handoff} progress={ease(t, 1.25, 1.82)} />
        <ShortCallout left={1270 - 180 * handoff} top={312 - 35 * handoff} progress={ease(t, 1.30, 1.78)}>本地入口</ShortCallout>
      </AbsoluteFill>
    );
  }
  if (t < 6.24) {
    const travel = ease(t, 3.20, 4.74);
    return (
      <AbsoluteFill style={{background: UI_DARK}}>
        <EvidenceCamera image="research" cx={520 + 55 * travel} cy={705 + 95 * travel} scale={2.1 + .28 * travel} dim={.18} />
        <Chrome section="01 · RESEARCH" />
        <Underline left={350} top={568} width={875} progress={ease(t, 3.32, 4.10)} />
        <div style={{position: 'absolute', left: 390 + 610 * travel, top: 315, width: 290, height: 118, background: '#fff', border: `4px solid ${YELLOW}`, color: INK, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 48, fontWeight: 800, zIndex: 18}}>候选</div>
        <div style={{position: 'absolute', left: 1355, top: 270, width: 12, height: 300, background: YELLOW, zIndex: 18}} />
        <ShortCallout left={1398} top={350} progress={ease(t, 4.52, 5.02)}>待确认</ShortCallout>
        <Label style={{left: 82, top: 158, color: '#9ca7b6', fontSize: 21, zIndex: 20}}>流程示意 · 背景为真实界面</Label>
      </AbsoluteFill>
    );
  }
  if (t < 7.34) {
    const p = ease(t, 6.24, 6.42);
    return (
      <AbsoluteFill style={{background: YELLOW}}>
        <Chrome section="REACTION" light />
        <Crop image="research" rect={[244, 804, 390, 34]} width={670} style={{left: 105, top: 535, opacity: .88, borderLeft: `6px solid ${INK}`}} />
        <Label style={{left: 130, top: 260, fontSize: 122, fontWeight: 800, color: INK, opacity: p}}>等等。</Label>
        <div style={{position: 'absolute', left: 142, top: 428, width: 260 * p, height: 14, background: RED}} />
        <Reaction progress={p} />
      </AbsoluteFill>
    );
  }
  if (t < 9.87) {
    const returnToEvidence = ease(t, 7.34, 7.85);
    return (
      <AbsoluteFill style={{background: UI_DARK}}>
        <EvidenceCamera image="research" cx={640} cy={815} scale={2.48} />
        <div style={{position: 'absolute', inset: 0, background: YELLOW, opacity: 1 - returnToEvidence}} />
        <Chrome section="01 · RESEARCH" />
        <Underline left={655} top={535} width={425} progress={ease(t, 7.62, 8.18)} />
        <ShortCallout left={1248} top={655} progress={ease(t, 7.90, 8.38)} tone="red">≠ FACT</ShortCallout>
      </AbsoluteFill>
    );
  }
  if (t < 11.88) {
    return <HumanReview characterWidth={500} evidenceLeft={630} evidenceWidth={1210} progress={ease(t, 9.95, 10.34)} />;
  }
  if (t < 12.75) {
    const leave = ease(t, 12.24, 12.72);
    return (
      <AbsoluteFill style={{background: '#fff'}}>
        <Chrome section="SOURCE → FACT" light />
        <Crop image="research" rect={[244, 804, 390, 34]} width={1020} style={{left: 100, top: 340, borderLeft: `7px solid ${YELLOW}`}} />
        <Character name="point" style={{left: 1220 + 520 * leave, top: 190, width: 570, height: 690}} />
      </AbsoluteFill>
    );
  }
  if (t < 15.42) {
    return <SourceFactRelation time={t} light start={12.75} />;
  }
  const zoom = ease(t, 15.42, 16.58);
  const enter = ease(t, 17.30, 17.55);
  return (
    <AbsoluteFill style={{background: UI_DARK}}>
      <EvidenceCamera image="script" cx={750 - 130 * zoom} cy={400 + 30 * zoom} scale={1.2 + 1.62 * zoom} />
      <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 320, background: 'linear-gradient(#0b1018f2,#0b101899,transparent)', opacity: zoom}} />
      <div style={{position: 'absolute', left: 0, top: 565, width: 1920, height: 330, background: 'linear-gradient(transparent,#0b1018ee)', opacity: zoom}} />
      <Chrome section="03 · SCRIPT" />
      <Underline left={604} top={540} width={322} progress={ease(t, 16.54, 17.08)} />
      <ShortCallout left={1190} top={694} progress={ease(t, 16.75, 17.22)}>引用要求</ShortCallout>
      <div style={{position: 'absolute', left: -490 + 500 * enter, top: 525, width: 420, height: 440, borderRadius: '50%', background: YELLOW, overflow: 'hidden', zIndex: 25}}>
        <Character name="point" style={{left: 18, top: 18, width: 390, height: 490}} />
      </div>
    </AbsoluteFill>
  );
};
