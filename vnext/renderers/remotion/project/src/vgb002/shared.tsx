import React from 'react';
import {AbsoluteFill, Img} from 'remotion';
import {asset, Character, Crop, ease, INK, Label, RED, YELLOW} from '../vgb001/shared';

export const UI_DARK = '#0b1018';

export const EvidenceCamera: React.FC<{
  image: 'research' | 'script';
  cx: number;
  cy: number;
  scale: number;
  dim?: number;
  opacity?: number;
}> = ({image, cx, cy, scale, dim = 0, opacity = 1}) => (
  <AbsoluteFill style={{background: UI_DARK, opacity}}>
    <Img
      src={asset(`${image}.png`)}
      style={{
        position: 'absolute',
        width: 1600 * scale,
        height: 1000 * scale,
        left: 960 - cx * scale,
        top: 500 - cy * scale,
        maxWidth: 'none',
      }}
    />
    {dim > 0 ? <AbsoluteFill style={{background: `rgba(4,8,12,${dim})`}} /> : null}
  </AbsoluteFill>
);

export const Chrome: React.FC<{section: string; light?: boolean}> = ({section, light = false}) => (
  <>
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        height: 118,
        background: light ? 'linear-gradient(#ffffff, #ffffffdd, transparent)' : 'linear-gradient(#0b1018f2, #0b1018c0, transparent)',
        zIndex: 20,
      }}
    />
    <Label style={{left: 76, top: 48, fontSize: 24, color: light ? INK : '#e8edf4', zIndex: 21}}>
      XIAO-Y <span style={{color: YELLOW}}>／</span> EVIDENCE EDITORIAL
    </Label>
    <Label style={{right: 76, top: 48, fontSize: 24, color: light ? '#62666b' : '#c4ccd8', zIndex: 21}}>{section}</Label>
  </>
);

export const ShortCallout: React.FC<{
  children: React.ReactNode;
  left: number;
  top: number;
  progress?: number;
  tone?: 'yellow' | 'red' | 'dark';
}> = ({children, left, top, progress = 1, tone = 'yellow'}) => {
  const bg = tone === 'red' ? RED : tone === 'dark' ? INK : YELLOW;
  const color = tone === 'yellow' ? INK : '#fff';
  return (
    <div style={{position: 'absolute', left, top, opacity: progress, translate: `${24 * (1 - progress)}px 0`, zIndex: 30}}>
      <div style={{fontSize: 34, fontWeight: 800, letterSpacing: 2, color, background: bg, padding: '12px 20px'}}>{children}</div>
    </div>
  );
};

export const Underline: React.FC<{left: number; top: number; width: number; progress: number; color?: string}> = ({left, top, width, progress, color = YELLOW}) => (
  <div style={{position: 'absolute', left, top, width: width * progress, height: 9, background: color, borderRadius: 8, zIndex: 15}} />
);

export const Reaction: React.FC<{progress: number; compact?: boolean}> = ({progress, compact = false}) => (
  <div
    style={{
      position: 'absolute',
      right: compact ? 70 : 0,
      top: compact ? 180 : 0,
      width: compact ? 440 : 920,
      height: compact ? 470 : 1080,
      background: YELLOW,
      borderRadius: compact ? '50%' : 0,
      opacity: progress,
      scale: .94 + .06 * progress,
      overflow: 'hidden',
      zIndex: 25,
    }}
  >
    <Character name="surprise" style={{left: compact ? 70 : 80, top: compact ? 15 : 55, width: compact ? 330 : 820, height: compact ? 520 : 1120, objectPosition: 'top'}} />
  </div>
);

export const HumanReview: React.FC<{characterWidth: number; evidenceLeft: number; evidenceWidth: number; progress: number}> = ({characterWidth, evidenceLeft, evidenceWidth, progress}) => (
  <AbsoluteFill style={{background: '#fff'}}>
    <Chrome section="HUMAN REVIEW" light />
    <div style={{position: 'absolute', left: 80, top: 165, width: characterWidth, height: 720, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 35, top: 110, width: characterWidth - 50, height: characterWidth - 50, borderRadius: '50%', background: YELLOW}} />
      <Character name="serious" style={{left: 0, top: 0, width: characterWidth, height: 720}} />
    </div>
    <Crop image="script" rect={[228, 575, 1030, 138]} width={evidenceWidth} style={{left: evidenceLeft, top: 235, boxShadow: '0 24px 60px #10131928'}} />
    <Crop image="script" rect={[228, 688, 650, 98]} width={evidenceWidth * .72} style={{left: evidenceLeft, top: 455, boxShadow: '0 18px 42px #10131920'}} />
    <ShortCallout left={evidenceLeft + 70} top={190} progress={progress}>人工把关</ShortCallout>
    <div style={{position: 'absolute', left: evidenceLeft + 62, top: 408, width: 690 * progress, height: 9, background: YELLOW}} />
  </AbsoluteFill>
);

export const SourceFactRelation: React.FC<{time: number; light?: boolean; start?: number}> = ({time, light = false, start = 11.88}) => {
  const line = ease(time, start + .30, start + 1.50);
  const collect = ease(time, start + 2.10, start + 2.65);
  const bg = light ? '#fff' : UI_DARK;
  const fg = light ? INK : '#f4f6f8';
  return (
    <AbsoluteFill style={{background: bg, color: fg}}>
      <Chrome section="SOURCE ↔ FACT" light={light} />
      <Label style={{left: 95, top: 148, color: light ? '#777' : '#aeb8c7', fontSize: 22}}>流程示意 · 非操作回放</Label>
      <Crop image="research" rect={[244, 804, 390, 34]} width={760} style={{left: 110 + 120 * collect, top: 310, borderLeft: `6px solid ${YELLOW}`, boxShadow: light ? '0 20px 50px #10131918' : '0 25px 70px #0008'}} />
      <Label style={{left: 110 + 120 * collect, top: 440, color: light ? '#555' : '#bac4d0', fontSize: 29}}>来源说明</Label>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <path d={`M${870 + 120 * collect} 392 H${1310 - 90 * collect}`} fill="none" stroke={YELLOW} strokeWidth="16" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - line} />
        <path d={`M${1310 - 90 * collect} 465 H${870 + 120 * collect}`} fill="none" stroke={light ? '#363636' : '#dce2ea'} strokeWidth="4" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - line} />
      </svg>
      <div style={{position: 'absolute', left: 1310 - 90 * collect, top: 305, width: 390, height: 180, background: YELLOW, color: INK, border: `4px solid ${INK}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 66, fontWeight: 800}}>Fact</div>
      <Label style={{left: 968, top: 516, color: light ? '#777' : '#b9c3cf', fontSize: 27, opacity: line * (1 - collect)}}>绑定与回溯</Label>
      <div style={{position: 'absolute', left: 205, top: 250, width: 1460, height: 340, border: `3px solid ${light ? INK : '#7d8897'}`, opacity: collect}} />
      <Label style={{left: 790, top: 626, color: fg, fontSize: 34, opacity: collect}}>FACT PACK</Label>
    </AbsoluteFill>
  );
};
