import React from 'react';
import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import {asset, Crop, ease, Label, Rect, YELLOW} from './shared';

const View:React.FC<{image:'research'|'script';cx:number;cy:number;scale:number;dim?:number}> = ({image,cx,cy,scale,dim=0}) => <AbsoluteFill style={{background:'#11161e'}}><Img src={asset(`${image}.png`)} style={{position:'absolute',width:1600*scale,height:1000*scale,left:960-cx*scale,top:500-cy*scale,maxWidth:'none'}}/>{dim>0&&<AbsoluteFill style={{background:`rgba(4,8,12,${dim})`}}/>}</AbsoluteFill>;
const locator:React.CSSProperties={height:8,background:YELLOW,position:'absolute'};
export const DirectionA:React.FC = () => {
 const t=useCurrentFrame()/30;
 const p=ease(t,.35,1.2), q=ease(t,2.91,3.65), r=ease(t,6.24,7.05), final=ease(t,15.42,16.45);
 return <AbsoluteFill style={{background:'#0c1016',color:'#fff'}}>
  {t<2.91&&<>
   <View image="research" cx={800-330*p} cy={455+142*p} scale={1.12+1.18*p}/>
   <div style={{...locator,left:492,top:650,width:190*ease(t,1.25,1.65)}}/>
   <Label style={{left:1160,top:420,fontSize:32,color:'#e9eaed',opacity:ease(t,1.3,1.7)}}>本地文件入口</Label>
   <svg style={{position:'absolute',inset:0}} width="1920" height="1080"><path d="M1130 439 H1030 L808 562" fill="none" stroke={YELLOW} strokeWidth="3" strokeDasharray="560" strokeDashoffset={560*(1-ease(t,1.4,1.9))}/></svg>
  </>}
  {t>=2.91&&t<9.87&&<>
   <View image="research" cx={470+30*q+70*r} cy={597+203*q+15*r} scale={2.30+.12*q+.20*r}/>
   {t>4&&<div style={{position:'absolute',left:0,top:0,width:1920,height:430,background:'linear-gradient(#0c1016dd,#0c1016aa,transparent)',opacity:ease(t,4,4.5)}}/>}
   <div style={{...locator,left:341+317*r,top:568-35*r,width:(910-480*r)*ease(t,4,4.8)}}/>
   <div style={{position:'absolute',left:0,top:620,width:1920,height:460,background:'linear-gradient(transparent,#0c1016 40%)',opacity:ease(t,4,4.5)}}/>
  </>}
  {t>=9.87&&t<11.88&&<>
   <View image="script" cx={600} cy={650} scale={2.32}/>
   <div style={{...locator,left:141,top:434,width:490*ease(t,9.95,10.4)}}/>
   <Label style={{left:1350,top:720,color:'#cbd2dd'}}>脚本侧的人工审查</Label>
  </>}
  {t>=11.88&&t<15.42&&<>
   <View image="script" cx={780} cy={500} scale={1.25} dim={.83}/>
   <Label style={{left:135,top:205,color:'#aeb9c8'}}>绑定关系 · 流程示意</Label>
   <Crop image="research" rect={[244,804,390,34]} width={780} style={{left:140,top:335,borderLeft:`5px solid ${YELLOW}`,boxShadow:'0 20px 60px #0006'}}/>
   <Label style={{left:140,top:470,fontSize:38}}>来源</Label>
   <svg width="1920" height="1080" style={{position:'absolute',inset:0}}><path d="M570 555 V640 H1230 V500" fill="none" stroke={YELLOW} strokeWidth="4" strokeDasharray="980" strokeDashoffset={980*(1-ease(t,12.2,13.65))}/></svg>
   <div style={{position:'absolute',left:1080,top:333,width:390,height:170,border:'1px solid #566271',background:'#17202b',padding:'30px 42px',boxSizing:'border-box',opacity:ease(t,12.6,13.2)}}><div style={{fontSize:64,letterSpacing:-2}}>Fact</div><div style={{fontSize:24,marginTop:8,color:'#b8c2d0'}}>保留来源关系</div></div>
   <Label style={{left:1090,top:710,fontSize:31,color:'#e4e8ed',opacity:ease(t,13.5,14.1)}}>Fact Pack</Label>
  </>}
  {t>=15.42&&<>
   <View image="script" cx={750-135*final} cy={400+29*final} scale={1.18+1.67*final}/>
   {final>.1&&<><div style={{position:'absolute',left:0,top:0,width:1920,height:330,background:'linear-gradient(#0c1016ee,#0c1016aa,transparent)',opacity:final}}/><div style={{position:'absolute',left:0,top:555,width:1920,height:380,background:'linear-gradient(transparent,#0c1016f0)',opacity:final}}/></>}
   <div style={{...locator,left:604,top:540,width:322*ease(t,16.5,17.15)}}/>
   <Label style={{left:1170,top:697,fontSize:32,color:'#cbd2dd',opacity:ease(t,17.1,17.5)}}>本次脚本方向中的引用要求</Label>
  </>}
  <div style={{position:'absolute',left:0,top:0,width:1920,height:140,background:'linear-gradient(#0b1019e6,transparent)'}}/>
  <Label style={{left:88,top:57,fontSize:24,color:'#bac7d7'}}>CONTENT OS / WORKBENCH</Label>
  <Label style={{right:88,top:57,fontSize:24,color:'#bac7d7'}}>{t<9.87?'01 · RESEARCH':t<11.88?'02 · HUMAN REVIEW':t<15.42?'RELATION STUDY':'03 · SCRIPT'}</Label>
 </AbsoluteFill>;
};
