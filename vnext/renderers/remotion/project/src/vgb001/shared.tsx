import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, delayRender, continueRender, cancelRender} from 'remotion';
export const FPS = 30;
export const FRAMES = 574;
export const YELLOW = '#FFC800';
export const RED = '#EF342C';
export const INK = '#101319';
export const asset = (name: string) => staticFile(`PREVIEW-VGB001/${name}`);
export const clamp = (v:number) => Math.max(0,Math.min(1,v));
export const ease = (t:number,a:number,b:number) => {const p=clamp((t-a)/(b-a));return p*p*(3-2*p);};
export type Rect = [number,number,number,number];
// Exact source pixels. rect is [x,y,width,height] in the 1600x1000 source.
export const Crop:React.FC<{image:'research'|'script';rect:Rect;width:number;style?:React.CSSProperties}> = ({image,rect:[x,y,w,h],width,style}) => <div style={{position:'absolute',width,height:width*h/w,overflow:'hidden',...style}}><Img src={asset(`${image}.png`)} style={{position:'absolute',width:1600*width/w,height:1000*width/w,maxWidth:'none',left:-x*width/w,top:-y*width/w}}/></div>;
export const Character:React.FC<{name:'point'|'think'|'serious'|'surprise';style?:React.CSSProperties}> = ({name,style}) => <Img src={asset(`${name}.png`)} style={{position:'absolute',objectFit:'contain',...style}}/>;
export const Label:React.FC<{children:React.ReactNode;style?:React.CSSProperties}> = ({children,style}) => <div style={{position:'absolute',fontSize:28,lineHeight:1.25,letterSpacing:1,...style}}>{children}</div>;
// Caption-compatible JSON shape, fixed across A/B/C. No speculative word timestamps.
export const captions = [
 {text:'研究页允许从本地文件导入资料',startMs:0,endMs:2910,timestampMs:null,confidence:null},
 {text:'模型提取的原文候选需要操作者确认',startMs:2910,endMs:6240,timestampMs:null,confidence:null},
 {text:'候选引文不会自动成为已核实 Fact',startMs:6240,endMs:9870,timestampMs:null,confidence:null},
 {text:'这一步必须由人来把关',startMs:9870,endMs:11880,timestampMs:null,confidence:null},
 {text:'Fact Pack 把选中的事实与来源绑定',startMs:11880,endMs:15420,timestampMs:null,confidence:null},
 {text:'脚本里的事实性主张要引用已有 Fact ID',startMs:15420,endMs:19120,timestampMs:null,confidence:null},
];
export const SoundAndCaptions:React.FC = () => {
 const t=useCurrentFrame()/FPS*1000;
 const cue=captions.find(c=>t>=c.startMs&&t<c.endMs);
 return <><Audio src={asset('voice.wav')}/>{cue&&<div data-caption="true" style={{position:'absolute',bottom:50,left:120,right:120,display:'flex',justifyContent:'center',zIndex:100}}><div style={{fontSize:42,lineHeight:1.25,whiteSpace:'pre',fontWeight:500,color:'#fff',background:'#101319',padding:'13px 24px',borderRadius:8}}>{cue.text}</div></div>}</>;
};
export const Film:React.FC<{children:React.ReactNode}> = ({children}) => {
 const [handle]=useState(()=>delayRender('VGB local pinned font'));
 useEffect(()=>{const font=new FontFace('VGB',`url(${asset('font.otf')})`);font.load().then(f=>{(document.fonts as unknown as {add:(f:FontFace)=>void}).add(f);continueRender(handle);}).catch(cancelRender);},[handle]);
 return <AbsoluteFill style={{fontFamily:'VGB, sans-serif',color:INK,background:'#fff',overflow:'hidden'}}>{children}<SoundAndCaptions/></AbsoluteFill>;
};
