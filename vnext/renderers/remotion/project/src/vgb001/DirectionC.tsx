import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Character, Crop, ease, INK, RED, YELLOW} from './shared';

// VGB only. Explanatory diagrams are never presented as captured application states.
const Mix = (a:number,b:number,p:number) => a+(b-a)*p;
const Small:React.FC<{children:React.ReactNode;style?:React.CSSProperties}> = ({children,style}) =>
  <div style={{position:'absolute',fontSize:27,letterSpacing:2,color:'#B6BDC6',...style}}>{children}</div>;
const Quote:React.FC<{x:number;y:number;size?:number;opacity?:number}> = ({x,y,size=200,opacity=1}) =>
  <div style={{position:'absolute',left:x,top:y,width:size,height:size,opacity,color:YELLOW,fontFamily:'Georgia, serif',fontSize:size*1.7,lineHeight:1,fontWeight:900}}>“</div>;
const Path:React.FC<{d:string;color?:string;length?:number;opacity?:number;width?:number;dash?:string}> = ({d,color=YELLOW,length=1,opacity=1,width=7,dash}) =>
  <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="square" opacity={opacity} pathLength={1} strokeDasharray={dash??'1'} strokeDashoffset={dash?0:1-length}/>;

export const DirectionC:React.FC = () => {
  const t=useCurrentFrame()/30;
  const extract=ease(t,2.40,3.24);
  const candidate=ease(t,3.10,4.85);
  const reject=ease(t,6.24,6.75);
  const gate=ease(t,9.87,10.30);
  const bind=ease(t,11.88,12.38);
  const script=ease(t,15.42,16.02);
  return <AbsoluteFill style={{background:INK,color:'#F5F5EF',overflow:'hidden'}}>
    {/* Continuous thin line changes from source margin to broken shortcut to provenance link. */}
    <div style={{position:'absolute',left:0,top:0,right:0,height:12,background:YELLOW}}/>
    <Small style={{top:54,left:70,color:'#fff'}}>XIAO-Y <span style={{color:YELLOW}}>／</span> EVIDENCE IN MOTION</Small>
    <Small style={{top:57,right:70,color:YELLOW}}>{t<2.9?'原始界面 · 研究入口':t<15.42?'流程示意 · 非操作录屏':'原始界面 · 脚本要求'}</Small>

    {/* Source UI is visible as source pixels, then leaves as the explanatory token enters. */}
    {t<3.24&&<div style={{position:'absolute',inset:0,transform:`translateY(${-570*extract}px)`,opacity:1-extract*.82}}>
      <div style={{position:'absolute',left:100,top:132,fontSize:104,fontWeight:900,letterSpacing:-3}}>入口，在这里。</div>
      <Crop image="research" rect={[235,491,1060,198]} width={1660} style={{left:130,top:328,transform:`scale(${Mix(.96,1,ease(t,0,.8))})`,transformOrigin:'50% 50%'}}/>
      <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
        <Path d="M 102 340 L 102 637 L 310 637" length={ease(t,.55,1.20)} width={9}/>
      </svg>
    </div>}

    {/* One quote token remains the protagonist instead of six independent title cards. */}
    {t>=2.40&&t<12.38&&<div style={{position:'absolute',inset:0,opacity:Math.min(extract,1-bind)}}>
      <div style={{position:'absolute',left:110,top:142,fontSize:98,fontWeight:900,opacity:1-gate}}>{t<6.24?'确认之前':'≠'}</div>
      <div style={{position:'absolute',left:1280,top:442,fontSize:110,fontWeight:900,color:t<6.24?'#66717D':'#CFD5DB',opacity:1-gate}}>FACT</div>
      <svg width="1920" height="1080" style={{position:'absolute',inset:0,opacity:1-gate}}>
        <Path d="M 600 535 L 940 535" length={ease(t,4.50,5.10)} color="#5D6875" width={6}/>
        <Path d="M 1000 535 L 1200 535" length={ease(t,5.10,5.65)} color="#5D6875" width={6} opacity={1-reject}/>
        <path d="M 1170 509 L 1200 535 L 1170 561" fill="none" stroke="#5D6875" strokeWidth="6" opacity={ease(t,5.15,5.6)*(1-reject)}/>
        <Path d="M 1030 410 L 950 660" color={RED} width={18} length={reject}/>
      </svg>
      <Quote x={Mix(400,620,candidate)-gate*100} y={Mix(398,432,candidate)-gate*60} size={205}/>
      <div style={{position:'absolute',left:Mix(370,610,candidate)-gate*100,top:650-gate*60,fontSize:46,fontWeight:700,color:YELLOW}}>候选引文</div>
      {/* Gate is explanatory, left closed: the source provides no successful confirmation capture. */}
      <div style={{position:'absolute',left:910,top:210,width:10,height:610,background:YELLOW,transform:`scaleY(${gate})`,transformOrigin:'50% 100%'}}/>
      <div style={{position:'absolute',left:980,top:285,fontSize:109,fontWeight:900,opacity:gate}}>确认权</div>
      <div style={{position:'absolute',left:988,top:541,width:218,height:6,background:YELLOW,transform:`scaleX(${ease(t,10.15,10.48)})`,transformOrigin:'0 0'}}/>
      {t>=10.20&&t<11.70&&<Character name="serious" style={{left:1350,top:438,width:240,height:276,opacity:ease(t,10.2,10.35)*(1-ease(t,11.45,11.7))}}/>}
    </div>}

    {/* The quote returns to its origin. The reciprocal path is the actual new information. */}
    {t>=11.88&&t<16.02&&<div style={{position:'absolute',inset:0,opacity:bind*(1-script),transform:`translateY(${-160*script}px)`}}>
      <div style={{position:'absolute',left:100,top:146,fontSize:106,fontWeight:900}}>溯源</div>
      <Crop image="research" rect={[245,502,710,178]} width={700} style={{left:110,top:405,opacity:.84}}/>
      <div style={{position:'absolute',left:125,top:618,fontSize:43,fontWeight:800}}>来源</div>
      <Quote x={610} y={555} size={105}/>
      <div style={{position:'absolute',left:1330,top:392,fontSize:112,fontWeight:900}}>FACT</div>
      <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
        <Path d="M 850 455 L 1240 455" length={ease(t,12.40,13.05)} width={8}/>
        <path d="M 1210 428 L 1240 455 L 1210 482" fill="none" stroke={YELLOW} strokeWidth="8" opacity={ease(t,12.86,13.05)}/>
        <Path d="M 1240 570 L 850 570" length={ease(t,13.12,13.78)} width={8}/>
        <path d="M 880 543 L 850 570 L 880 597" fill="none" stroke={YELLOW} strokeWidth="8" opacity={ease(t,13.56,13.78)}/>
      </svg>
    </div>}

    {/* Match the diagram's FACT to the actual Fact ID text, not a fabricated validated claim. */}
    {t>=15.42&&<div style={{position:'absolute',inset:0,opacity:script}}>
      <div style={{position:'absolute',left:100,top:136,fontSize:144,fontWeight:900,letterSpacing:-3}}>FACT<span style={{color:YELLOW,display:'inline-block',marginLeft:28,transform:`translateX(${60*(1-ease(t,15.64,16.20))}px)`,opacity:ease(t,15.64,16.2)}}>ID</span></div>
      <Small style={{left:114,top:330,color:'#fff'}}>引用要求</Small>
      <Crop image="script" rect={[240,350,1050,112]} width={1680} style={{left:112,top:438}}/>
      <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
        <Path d="M 88 430 L 88 642 L 1808 642 L 1808 430" length={ease(t,16.12,16.74)} width={7}/>
      </svg>
      <Small style={{left:116,top:696}}>脚本方向 · 原始截图</Small>
    </div>}
  </AbsoluteFill>;
};
