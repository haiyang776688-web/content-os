import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Character, Crop, ease, INK, Label, RED, YELLOW} from './shared';

const Mark:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{position:'absolute',fontSize:30,letterSpacing:2,fontWeight:700,...style}}>{children}</div>;
const Demo=()=> <Label style={{left:80,top:62,color:'#737373',fontSize:24}}>流程示意 · 非界面操作回放</Label>;
const Arrow:React.FC<{x:number;y:number;w:number;progress:number;color?:string}>=({x,y,w,progress,color=INK})=><svg style={{position:'absolute',left:x,top:y,width:w,height:80,overflow:'visible'}} viewBox={`0 0 ${w} 80`}><path d={`M0 40H${w-22}l-22 -20m22 20l-22 20`} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/></svg>;
const FactTicket:React.FC<{label:string;style?:React.CSSProperties}>=({label,style})=><div style={{position:'absolute',width:370,height:190,background:YELLOW,border:`5px solid ${INK}`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:72,fontWeight:800,...style}}>{label}</div>;

/** VGB-001 B: a hand-authored editorial sample, independent of production entry. */
export const DirectionB:React.FC=()=>{
 const t=useCurrentFrame()/30;
 if(t<2.91){
  const push=ease(t,.75,1.42);
  return <AbsoluteFill style={{background:'#fff'}}>
   <Mark style={{left:80,top:60}}>XIAO-Y <span style={{color:'#999',fontWeight:400}}> / 内容从哪来</span></Mark>
   <Character name="point" style={{left:80-660*push,top:240,width:560,height:600}}/>
   <Crop image="research" rect={[246,523,400,156]} width={1040+460*push} style={{left:740-480*push,top:290-70*push,boxShadow:'0 16px 45px #10131920'}}/>
   <Label style={{left:740-480*push,top:225-70*push,fontSize:30,color:'#555'}}>研究界面 · 真实截图</Label>
   <svg style={{position:'absolute',left:0,top:0,width:1920,height:900}}>
    <path d={`M${820-480*push} ${595+47*push}h${(360+140*push)*ease(t,1.55,1.98)}`} stroke={YELLOW} strokeWidth="12" strokeLinecap="round" opacity={ease(t,1.55,1.6)}/>
   </svg>
  </AbsoluteFill>;
 }
 if(t<6.24){
  const travel=ease(t,3.2,4.55);const reveal=ease(t,4.15,4.65);
  return <AbsoluteFill style={{background:'#fff'}}><Demo/>
   <div style={{position:'absolute',left:180,top:258,width:310,height:395,border:`5px solid ${INK}`,background:'#fafafa'}}>
    <Mark style={{left:35,top:32,fontSize:35}}>原文</Mark>
    {[0,1,2,3].map(i=><div key={i} style={{position:'absolute',left:35,top:112+i*52,width:i===3?130:235,height:9,background:i===1?YELLOW:'#bfc1c4'}}/>)}
   </div>
   <Arrow x={515} y={396} w={405} progress={ease(t,3.0,3.55)}/>
   <FactTicket label="候选" style={{left:500+420*travel,top:344,background:'#fff',width:310,height:210}}/>
   <div style={{position:'absolute',left:1400,top:235,height:440,width:18,background:INK}}/>
   <div style={{position:'absolute',left:1418,top:235,width:295,height:440,background:'#f2f2f2',opacity:reveal}}/>
   <Mark style={{left:1458,top:370,fontSize:58,opacity:reveal}}>待确认</Mark>
   <div style={{position:'absolute',left:1150,top:580,width:190,height:8,background:YELLOW,scale:`${reveal} 1`,transformOrigin:'left'}}/>
   <Label style={{left:925,top:625,fontSize:38,opacity:reveal}}>到这里，先停下</Label>
  </AbsoluteFill>;
 }
 if(t<7.34){
  const cut=ease(t,6.24,6.42);
  return <AbsoluteFill style={{background:YELLOW}}>
   <Mark style={{left:145,top:245,fontSize:126,lineHeight:1.13}}>等等。</Mark>
   <div style={{position:'absolute',left:665,top:75,width:1120,height:1005,overflow:'hidden'}}>
    <Character name="surprise" style={{left:70,top:0,width:1020+60*cut,height:1510,objectPosition:'top'}}/>
   </div>
   <div style={{position:'absolute',left:165,top:460,width:270,height:14,background:RED}}/>
  </AbsoluteFill>;
 }
 if(t<9.87){
  const snap=ease(t,7.34,7.6);
  return <AbsoluteFill style={{background:'#fff'}}><Demo/>
   <FactTicket label="候选" style={{left:190,top:330,width:480,height:250,background:'#fff'}}/>
   <FactTicket label="Fact" style={{left:1250,top:330,width:480,height:250,background:'#fff',color:'#828282',borderColor:'#c9c9c9'}}/>
   <div style={{position:'absolute',left:814,top:210,fontSize:280,fontWeight:800,lineHeight:1.7,color:RED,scale:`${.82+.18*snap}`}}>≠</div>
  </AbsoluteFill>;
 }
 if(t<11.88){
  const p=ease(t,10.0,10.45);
  return <AbsoluteFill style={{background:'#fff'}}><Demo/>
   <div style={{position:'absolute',left:1185,top:215,width:530,height:430,background:YELLOW}}/>
   <Character name="serious" style={{left:190,top:190,width:640,height:670}}/>
   <div style={{position:'absolute',left:885,top:338,width:665,height:165,border:`7px solid ${INK}`,background:'#fff',display:'flex',justifyContent:'center',alignItems:'center',fontSize:80,fontWeight:800,translate:`${50*(1-p)}px 0`}}>人工把关</div>
  </AbsoluteFill>;
 }
 if(t<15.42){
  const bind=ease(t,12.3,13.4);const collect=ease(t,14.25,14.8);
  return <AbsoluteFill style={{background:'#fff'}}><Demo/>
   <Mark style={{left:110,top:158,fontSize:45}}>FACT PACK</Mark>
   <div style={{position:'absolute',left:200+230*collect,top:305,width:420,height:320,border:`5px solid ${INK}`,background:'#fff'}}>
    <Mark style={{left:40,top:45,fontSize:52}}>来源</Mark>
    {[0,1,2].map(i=><div key={i} style={{position:'absolute',left:40,top:139+i*44,width:i===2?170:310,height:8,background:'#b6b9be'}}/>)}
   </div>
   <svg style={{position:'absolute',left:0,top:0,width:1920,height:900}}>
    <path d={`M${622+230*collect} 465H${1290-190*collect}`} stroke={INK} strokeWidth="7" fill="none" pathLength="1" strokeDasharray="1" strokeDashoffset={1-bind}/>
    <path d={`M${622+230*collect} 465H${1290-190*collect}`} stroke={YELLOW} strokeWidth="30" fill="none" pathLength="1" strokeDasharray="1" strokeDashoffset={1-bind}/>
   </svg>
   <FactTicket label="Fact" style={{left:1290-190*collect,top:370,width:390,height:190}}/>
   <Label style={{left:872,top:554,opacity:bind*(1-collect),fontSize:34}}>绑定</Label>
   <div style={{position:'absolute',left:365,top:256,width:1190,height:437,border:`3px solid ${INK}`,opacity:collect}}/>
  </AbsoluteFill>;
 }
 const punch=ease(t,16.65,17.18);
 return <AbsoluteFill style={{background:INK}}>
  <Mark style={{left:100,top:72,fontSize:30,color:'#aaa'}}>脚本方向 · 真实截图</Mark>
  <div style={{position:'absolute',left:0,top:326,width:1920,height:355,background:INK}}/>
  <div style={{opacity:1-punch}}><Crop image="script" rect={[235,386,1060,80]} width={1760} style={{left:80,top:420}}/></div>
  <div style={{opacity:punch}}><Crop image="script" rect={[465,420,355,30]} width={1420} style={{left:250,top:414}}/></div>
  <div style={{position:'absolute',left:602,top:559,width:230*ease(t,17.3,17.72),height:13,background:YELLOW}}/>
 </AbsoluteFill>;
};
