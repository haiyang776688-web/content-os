import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, cancelRender, continueRender,
  delayRender, interpolate, staticFile, useCurrentFrame,
} from 'remotion';
import motionContractJson from './motion-primitive-contract-v1.json';

type MotionContractEntry={allowed_layer_kinds:string[];behavior_class:string;
  renderer_consumer:string;implemented:boolean};
type MotionContract={contract_id:string;primitives:Record<string,MotionContractEntry>};
const motionContract=motionContractJson as MotionContract;

type Box = {width?:number;height?:number};
type Region = {x:number;y:number;width:number;height:number};
type MediaTransform = {fit_mode:string;scale_x:number;scale_y:number;render_width:number;
  render_height:number;left:number;top:number;destination_width:number;destination_height:number};
type MotionKeyframe={frame:number;value:number};
type CompiledMotionDesign={contract_id:string;phrase_id:string;intent:string;
  motion_role:'PRIMARY'|'SECONDARY'|'BACKGROUND';phase_offset_frames:number;
  primitive_progress:MotionKeyframe[];uniform_scale:MotionKeyframe[];
  opacity_multiplier?:MotionKeyframe[]};
type Meta = {
  layer_kind?:string;asset_src?:string;text?:string;box?:Box;color?:string;
  source_region?:Region|null;style_token?:string;z_index?:number;
  from_label?:string;to_label?:string;
  motion_primitive?:string;
  geometry_kind?:string;aspect_ratio_policy?:string;fit_mode?:string;
  intrinsic_width?:number;intrinsic_height?:number;intrinsic_aspect_ratio?:number;
  media_transform?:MediaTransform;asset_kind?:string;
  motion_design?:CompiledMotionDesign;
};
type Clip = {
  clip_id:string;track:string;timeline_in:number;timeline_out:number;
  source_in:number;source_out:number;position:{x:number;y:number};opacity:number;
  motion:Record<string,string>;metadata:Meta;muted?:boolean;
};
export type VREProps = {
  clips:Clip[];fps:number;width:number;height:number;duration_frames:number;
  font_src:string;visual_mode:string;
};

const url=(src:string)=>src.startsWith('/')||/^https?:/.test(src)?src:staticFile(src);
const smooth=(frame:number,end=12)=>interpolate(frame,[0,end],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const sampleKeyframes=(frame:number,keyframes:MotionKeyframe[])=>interpolate(
  frame,keyframes.map(keyframe=>keyframe.frame),keyframes.map(keyframe=>keyframe.value),
  {extrapolateLeft:'clamp',extrapolateRight:'clamp'});

export const assertMotionPrimitive=(primitive:string,layerKind:string):MotionContractEntry=>{
  const entry=motionContract.primitives[primitive];
  if(!entry) throw new Error(`MOTION_PRIMITIVE_UNKNOWN:${primitive}`);
  if(!entry.implemented||!entry.renderer_consumer){
    throw new Error(`MOTION_PRIMITIVE_DECLARED_NOT_RENDERED:${primitive}`);
  }
  if(!entry.allowed_layer_kinds.includes(layerKind)){
    throw new Error(`MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER:${primitive}:${layerKind}`);
  }
  return entry;
};

export const motionFrameState=(primitive:string,p:number):Record<string,number>=>{
  const entry=motionContract.primitives[primitive];
  if(!entry) throw new Error(`MOTION_PRIMITIVE_UNKNOWN:${primitive}`);
  const progress=Math.max(0,Math.min(1,p));
  switch(entry.behavior_class){
    case 'STATIC': return {static:1};
    case 'UNIFORM_SCALE_IN': return {uniformScale:.92+.08*progress};
    case 'OPACITY_REVEAL': return {opacity:progress};
    case 'TRANSLATE_IN': return {translateXPercent:-5*(1-progress)};
    case 'CLIP_WIPE': return {clipRightPercent:100*(1-progress),translateXPercent:-3*(1-progress)};
    case 'UNIFORM_POP_IN': return {uniformScale:.82+.18*progress};
    case 'RETURN_SETTLE': return {opacity:progress,uniformScale:1.05-.05*progress};
    case 'PATH_DRAW': return {pathReveal:progress};
    case 'UNIFORM_SETTLE': return {uniformScale:1.025-.025*progress};
    case 'WIDTH_REVEAL': return {widthRatio:progress};
    case 'LABEL_REVEAL': return {opacity:progress,translateXPx:24*(1-progress)};
    default: throw new Error(`MOTION_PRIMITIVE_DECLARED_NOT_RENDERED:${primitive}`);
  }
};

const AssetMedia:React.FC<{meta:Meta}>=({meta})=>{
  const transform=meta.media_transform!;
  const style:React.CSSProperties={position:'absolute',maxWidth:'none',maxHeight:'none',
    width:transform.render_width,height:transform.render_height,left:transform.left,top:transform.top};
  if(meta.asset_kind==='VIDEO') return <OffthreadVideo muted src={url(meta.asset_src!)} style={style}/>;
  return <Img src={url(meta.asset_src!)} style={style}/>;
};

const Layer:React.FC<{clip:Clip}>=({clip})=>{
  const frame=useCurrentFrame();
  const meta=clip.metadata;
  const design=meta.motion_design;
  const p=design?sampleKeyframes(frame,design.primitive_progress):smooth(frame);
  const primitive=clip.motion?.primitive??meta.motion_primitive??'NONE';
  const layerKind=meta.layer_kind??'UNKNOWN';
  assertMotionPrimitive(primitive,layerKind);
  const state=motionFrameState(primitive,p);
  const box=meta.box??{};
  const base:React.CSSProperties={position:'absolute',left:`${clip.position.x*100}%`,top:`${clip.position.y*100}%`,
    width:`${(box.width??.5)*100}%`,height:`${(box.height??.5)*100}%`,zIndex:meta.z_index??1,
    translate:'-50% -50%',opacity:clip.opacity??1,overflow:'hidden'};
  if('opacity' in state) base.opacity=state.opacity;
  if('uniformScale' in state) base.scale=state.uniformScale;
  if(design){
    const designScale=sampleKeyframes(frame,design.uniform_scale);
    base.scale=(typeof base.scale==='number'?base.scale:1)*designScale;
    if(design.opacity_multiplier){
      const opacityMultiplier=sampleKeyframes(frame,design.opacity_multiplier);
      base.opacity=(typeof base.opacity==='number'?base.opacity:1)*opacityMultiplier;
    }
  }
  if('translateXPercent' in state) base.translate=`${-50+state.translateXPercent}% -50%`;
  if('clipRightPercent' in state) base.clipPath=`inset(0 ${state.clipRightPercent}% 0 0)`;

  if(meta.layer_kind==='BACKGROUND') return <div style={{...base,background:meta.color}}/>;
  if(meta.layer_kind==='EVIDENCE') return <div style={{...base,boxShadow:'0 22px 58px #05080d38',borderRadius:8}}><AssetMedia meta={meta}/></div>;
  if(meta.layer_kind==='CHARACTER') return <div style={base}><AssetMedia meta={meta}/></div>;
  if(meta.layer_kind==='UNDERLINE') return <div style={{...base,width:`${(box.width??.4)*(state.widthRatio??1)*100}%`,background:meta.color??'#FFC800',borderRadius:12}}/>;
  if(meta.layer_kind==='RELATION') return <svg viewBox="0 0 1000 300" style={base} preserveAspectRatio="none">
    <path d="M30 95 H920 L850 35 M920 95 L850 155" pathLength="1" stroke={meta.color??'#FFC800'} strokeWidth="30" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="1" strokeDashoffset={1-(state.pathReveal??1)}/>
    <path d="M920 220 H90 L155 165 M90 220 L155 275" pathLength="1" stroke="#101319" strokeWidth="10" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="1" strokeDashoffset={1-(state.pathReveal??1)}/>
  </svg>;
  if(meta.layer_kind==='FACT_NODE') return <div style={{...base,display:'flex',alignItems:'center',justifyContent:'center',background:'#FFC800',border:'4px solid #101319',fontSize:68,fontWeight:900}}>Fact</div>;
  if(meta.layer_kind==='CALLOUT'){
    const red=meta.style_token==='RED_CALLOUT';
    return <div style={{...base,height:'auto',overflow:'visible',fontSize:42,fontWeight:900,letterSpacing:2,color:red?'#fff':'#101319',textAlign:'center'}}><span style={{display:'inline-block',background:red?'#EF342C':'#FFC800',padding:'12px 21px',opacity:state.opacity??1,translate:`${state.translateXPx??0}px 0`}}>{meta.text}</span></div>;
  }
  if(meta.layer_kind==='CHROME') return <div style={{...base,height:'auto',overflow:'visible',fontSize:23,fontWeight:700,letterSpacing:1.5,color:meta.color??'#dce2ea',textShadow:meta.color==='#101319'?'none':'0 2px 8px #0008'}}>{meta.text}</div>;
  if(meta.layer_kind==='SUBTITLE') return <div data-caption="true" style={{...base,height:'auto',overflow:'visible',display:'flex',justifyContent:'center',fontSize:42,fontWeight:500,color:'#fff',whiteSpace:'nowrap'}}><span style={{background:'#101319',padding:'13px 24px',borderRadius:8}}>{meta.text}</span></div>;
  return null;
};

export const Renderer:React.FC<VREProps>=(props)=>{
  const [handle]=useState(()=>delayRender('VRE-001 pinned font'));
  useEffect(()=>{const font=new FontFace('VRE',`url(${url(props.font_src)})`);font.load().then(f=>{(document.fonts as unknown as {add:(face:FontFace)=>void}).add(f);continueRender(handle);}).catch(cancelRender);},[handle,props.font_src]);
  return <AbsoluteFill style={{background:'#0B1018',fontFamily:'VRE, sans-serif',overflow:'hidden'}}>
    {props.clips.filter(c=>c.track!=='VOICE').map(c=><Sequence key={c.clip_id} from={Math.round(c.timeline_in*props.fps)} durationInFrames={Math.max(1,Math.round((c.timeline_out-c.timeline_in)*props.fps))}><Layer clip={c}/></Sequence>)}
    {props.clips.filter(c=>c.track==='VOICE').map(c=><Sequence key={c.clip_id} from={Math.round(c.timeline_in*props.fps)} durationInFrames={Math.max(1,Math.round((c.timeline_out-c.timeline_in)*props.fps))}><Audio src={url(c.metadata.asset_src!)} startFrom={Math.round(c.source_in*props.fps)} volume={c.muted?0:1}/></Sequence>)}
  </AbsoluteFill>;
};
