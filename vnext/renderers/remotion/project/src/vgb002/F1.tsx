import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Character, Crop, ease, YELLOW} from '../vgb001/shared';
import {Chrome, EvidenceCamera, HumanReview, Reaction, ShortCallout, SourceFactRelation, Underline, UI_DARK} from './shared';

export const F1: React.FC = () => {
  const t = useCurrentFrame() / 30;
  if (t < 2.91) {
    const handoff = ease(t, .48, 1.18);
    return (
      <AbsoluteFill style={{background: UI_DARK}}>
        <div style={{position: 'absolute', inset: 0, opacity: handoff}}>
          <EvidenceCamera image="research" cx={590 - 120 * handoff} cy={525 + 64 * handoff} scale={1.72 + .58 * handoff} />
        </div>
        <div style={{position: 'absolute', inset: 0, background: '#fff', opacity: 1 - handoff}}>
          <Chrome section="01 · RESEARCH" light />
          <Character name="point" style={{left: 75 - 650 * handoff, top: 235, width: 500, height: 620}} />
          <Crop image="research" rect={[245, 493, 430, 205]} width={1080} style={{left: 700 - 225 * handoff, top: 270 - 30 * handoff, boxShadow: '0 22px 55px #10131924'}} />
        </div>
        <Chrome section="01 · RESEARCH" />
        <Underline left={500} top={632} width={310} progress={ease(t, 1.18, 1.72)} />
        <ShortCallout left={1115} top={310} progress={ease(t, 1.25, 1.72)}>本地入口</ShortCallout>
      </AbsoluteFill>
    );
  }
  if (t < 9.87) {
    const move = ease(t, 2.91, 3.75);
    const focus = ease(t, 6.24, 7.06);
    const reactIn = ease(t, 6.24, 6.48) * (1 - ease(t, 6.95, 7.35));
    return (
      <AbsoluteFill style={{background: UI_DARK}}>
        <EvidenceCamera image="research" cx={500 + 60 * move + 70 * focus} cy={675 + 125 * move + 10 * focus} scale={2.02 + .28 * move + .18 * focus} dim={.10 * reactIn} />
        <Chrome section="01 · RESEARCH" />
        <Underline left={346 + 305 * focus} top={568 - 32 * focus} width={920 - 495 * focus} progress={ease(t, 3.65, 4.42)} />
        {t < 6.24 ? <ShortCallout left={1240} top={690} progress={ease(t, 4.45, 5.02)}>需人工确认</ShortCallout> : null}
        {t >= 6.24 ? <>
          <Reaction progress={reactIn} compact />
          <ShortCallout left={1325} top={685} progress={ease(t, 7.20, 7.72)} tone="red">≠ FACT</ShortCallout>
        </> : null}
      </AbsoluteFill>
    );
  }
  if (t < 11.88) {
    return <HumanReview characterWidth={430} evidenceLeft={560} evidenceWidth={1280} progress={ease(t, 9.96, 10.38)} />;
  }
  if (t < 15.42) {
    return <SourceFactRelation time={t} />;
  }
  const zoom = ease(t, 15.42, 16.52);
  const character = ease(t, 18.25, 18.56);
  return (
    <AbsoluteFill style={{background: UI_DARK}}>
      <EvidenceCamera image="script" cx={750 - 130 * zoom} cy={400 + 30 * zoom} scale={1.2 + 1.62 * zoom} />
      <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 320, background: 'linear-gradient(#0b1018f2,#0b101899,transparent)', opacity: zoom}} />
      <div style={{position: 'absolute', left: 0, top: 565, width: 1920, height: 330, background: 'linear-gradient(transparent,#0b1018ee)', opacity: zoom}} />
      <Chrome section="03 · SCRIPT" />
      <Underline left={604} top={540} width={322} progress={ease(t, 16.52, 17.12)} />
      <ShortCallout left={1180} top={694} progress={ease(t, 16.80, 17.30)}>引用要求</ShortCallout>
      <div style={{position: 'absolute', left: -430 + 440 * character, top: 565, width: 370, height: 390, borderRadius: '50%', background: YELLOW, overflow: 'hidden', zIndex: 25}}>
        <Character name="point" style={{left: 18, top: 22, width: 335, height: 430}} />
      </div>
    </AbsoluteFill>
  );
};
