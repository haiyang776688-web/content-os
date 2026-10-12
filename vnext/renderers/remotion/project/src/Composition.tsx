import React, {useEffect, useState} from 'react';
import {loadFont} from '@remotion/fonts';
import {AbsoluteFill, Audio, Composition, Img, OffthreadVideo, Sequence, staticFile, registerRoot, delayRender, continueRender, cancelRender, useCurrentFrame, interpolate} from 'remotion';

type Clip = {clip_id:string;track:string;timeline_in:number;timeline_out:number;source_in:number;source_out:number;asset_src?:string;media_kind?:string;hidden?:boolean;muted?:boolean;position?:{x:number;y:number};scale?:number;opacity?:number;crop?:{left?:number;top?:number;right?:number;bottom?:number};pattern_id?:string;motion?:{kind?:string;continuous?:'SLOW_ZOOM'|'SLOW_PAN';amount?:number};reveal?:{delay?:number};metadata?:{text?:string;typography_role?:string;treatment?:{kind:string;index:number;accent:string;ink:string;header?:string};portrait_window?:{x:number;y:number;w:number;h:number};box?:{width?:number;height?:number}}};
type Font = {font_id:string;src:string;weight:number;style:string;axes:{tag:string;min:number;max:number}[]};
type FontRole = {font_id:string;weight:number;size:number;letter_spacing:number;line_height:number;shadow:string};
export type Props = {clips:Clip[];fallback_title:string;character_src?:string;fps:number;width:number;height:number;duration_frames:number;canvas_color?:string;foreground_color?:string;phase2?:boolean;resolved_visual_composition?:unknown;audio_timing_map?:unknown;fonts?:Font[];typography?:{roles:Record<string,FontRole>;production_policy:string;fallback_font_id?:string}};
export const defaults:Props={clips:[],fallback_title:'Content OS vNext',fps:30,width:1280,height:720,duration_frames:150};
const assetUrl=(src:string)=>src.startsWith('/')||/^https?:/.test(src)?src:staticFile(src);
const styleFor=(clip:Clip):React.CSSProperties=>({position:'absolute',left:`${(clip.position?.x??.5)*100}%`,top:`${(clip.position?.y??.5)*100}%`,width:`${(clip.metadata?.box?.width??(clip.track==='CHARACTER'?.38:.8))*100}%`,height:`${(clip.metadata?.box?.height??.8)*100}%`,objectFit:'contain',transform:`translate(-50%,-50%) scale(${clip.scale??1})`,opacity:clip.opacity??1,clipPath:clip.crop?`inset(${(clip.crop.top??0)*100}% ${(clip.crop.right??0)*100}% ${(clip.crop.bottom??0)*100}% ${(clip.crop.left??0)*100}%)`:undefined});
const ClipView:React.FC<{c:Clip;props:Props}>=({c,props})=>{
  const frame=useCurrentFrame();
  const {fps,fallback_title,typography}=props;
  const reveal=Math.round((c.reveal?.delay??0)*fps);
  const visibility=c.motion?.kind==='HOLD'?(frame>=reveal?1:0):interpolate(frame,[reveal,reveal+8],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const durationFrames=Math.max(2,Math.round((c.timeline_out-c.timeline_in)*fps));
  const progress=interpolate(frame,[0,durationFrames-1],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const continuous=['MEDIA','VIDEO','CHARACTER'].includes(c.track)?c.motion?.continuous:undefined;
  const amount=Math.min(.05,Math.max(0,c.motion?.amount??0));
  const zoom=continuous==='SLOW_ZOOM'?1+amount*progress:1;
  const pan=continuous==='SLOW_PAN'?(progress-.5)*amount*320:0;
  const rise=c.motion?.kind==='SLIDE_UP'?interpolate(frame,[reveal,reveal+8],[20,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}):0;
  const role=typography?.roles[c.track==='SUBTITLE'?'SUBTITLE':c.metadata?.typography_role??'BODY'];
  const selected=props.fonts?.find(f=>f.font_id===role?.font_id);
  const family=role?`COS-${role.font_id}`+(typography?.production_policy==='ALLOW_FALLBACK'&&typography.fallback_font_id?`, COS-${typography.fallback_font_id}`:''):'Arial, sans-serif';
  const base:React.CSSProperties={...styleFor(c),opacity:(c.opacity??1)*visibility,
    transform:`translate(-50%,-50%) scale(${(c.scale??1)*zoom})`,
    translate:pan||rise?`${pan}px ${rise}px`:undefined};
  const textStyle:React.CSSProperties={...base,height:'auto',width:c.metadata?.box?.width?`${c.metadata.box.width*100}%`:c.track==='SUBTITLE'?'90%':c.pattern_id==='A_B_COMPARE'?'36%':c.pattern_id?.startsWith('CHARACTER_')?'50%':'80%',fontFamily:family,fontSynthesis:'none',fontStyle:selected?.style??'normal',fontSize:role?.size??(c.track==='SUBTITLE'?40:66),fontWeight:role?.weight??800,letterSpacing:role?.letter_spacing??0,lineHeight:role?.line_height??1.15,whiteSpace:c.track==='SUBTITLE'?'nowrap':'pre-wrap',textAlign:'center',color:c.track==='SUBTITLE'?'#fff':props.foreground_color??'#111',textShadow:c.track==='SUBTITLE'?role?.shadow??'0 2px 4px #0008':undefined,background:'transparent'};
  const rate=(c.source_out-c.source_in)/(c.timeline_out-c.timeline_in);
  const treatment=c.metadata?.treatment;
  const draw=interpolate(frame,[reveal+4,reveal+16],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const window=c.metadata?.portrait_window;
  const numbered=treatment&&['NUMBERED','CHECKLIST'].includes(treatment.kind)&&/^\d  /.test(c.metadata?.text??'');
  // Decorations and motion are frame functions: seeking, stills and export agree.
  const decorated:React.CSSProperties=treatment?{...textStyle,color:treatment.ink,
    background:treatment.kind==='COMPARE'?treatment.accent:'transparent',
    borderRadius:treatment.kind==='COMPARE'?24:0,
    translate:c.motion?.kind==='SLIDE_UP'?base.translate:undefined,
    transform:`translate(-50%,-50%) scale(${interpolate(frame,[reveal,reveal+10],[.96,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})})`}:textStyle;
  return <>
    {['TEXT','SUBTITLE'].includes(c.track)?<div style={decorated}>
      <span style={{position:'relative',display:'inline-block'}}>
        {treatment&&['MARKER','UNDERLINE'].includes(treatment.kind)?<svg viewBox="0 0 1000 40" preserveAspectRatio="none" style={{position:'absolute',left:'-2%',bottom:'-.09em',width:'104%',height:'.22em',zIndex:0,clipPath:`inset(0 ${(1-draw)*100}% 0 0)`}}><path d="M10 28 Q180 13 350 20 T650 16 T985 22" fill="none" stroke={treatment.accent} strokeWidth="21" strokeLinecap="round"/></svg>:null}
        <span style={{position:'relative',zIndex:1,...(c.track==='SUBTITLE'?{display:'inline-block',background:'rgba(13,19,24,0.88)',padding:'0.16em 0.45em',borderRadius:12,textShadow:'none'}:{})}}>{numbered?<><span style={{display:'inline-block',width:'.9em',height:'.9em',lineHeight:'.9em',marginRight:'.25em',borderRadius:'50%',background:treatment!.index%2?'#FFD51E':'#F21E2C',color:treatment!.index%2?'#111':'#fff'}}>{c.metadata!.text!.slice(0,1)}</span>{c.metadata!.text!.slice(3)}</>:c.metadata?.text||fallback_title}</span>
      </span>
    </div>:null}
    {['MEDIA','VIDEO','CHARACTER','ELEMENT'].includes(c.track)&&c.asset_src&&c.media_kind==='VIDEO'?<OffthreadVideo src={assetUrl(c.asset_src)} startFrom={Math.round(c.source_in*fps)} playbackRate={rate} muted={c.muted} style={base}/>:null}
    {['MEDIA','VIDEO','CHARACTER','ELEMENT'].includes(c.track)&&c.asset_src&&c.media_kind!=='VIDEO'?(window?
      <div style={{...base,overflow:'hidden'}}><Img src={assetUrl(c.asset_src)} style={{position:'absolute',width:`${100/window.w}%`,maxWidth:'none',left:`${-window.x/window.w*100}%`,top:`${-window.y/window.h*100}%`}}/></div>:
      <Img src={assetUrl(c.asset_src)} style={base}/>):null}
    {['VOICE','BGM','SFX'].includes(c.track)&&c.asset_src?<Audio src={assetUrl(c.asset_src)} startFrom={Math.round(c.source_in*fps)} playbackRate={rate} volume={c.muted?0:1}/>:null}
  </>;
};
export const scene:React.FC<Props>=(props)=>{
  const {clips,fallback_title,character_src,fps,fonts}=props;
  const [handle]=useState(()=>delayRender('Pinned project fonts'));
  useEffect(()=>{
    Promise.all((fonts??[]).map(f=>{const axis=f.axes.find(a=>a.tag==='wght');return loadFont({family:`COS-${f.font_id}`,url:assetUrl(f.src),weight:axis?`${axis.min} ${axis.max}`:String(f.weight),style:f.style});}))
      .then(()=>continueRender(handle)).catch(e=>cancelRender(e));
  },[handle,fonts]);
  return <AbsoluteFill style={{background:props.canvas_color??'#fff',color:'#111',fontFamily:'Arial, sans-serif'}}>
  {!props.phase2&&character_src&&!clips.some(c=>c.track==='CHARACTER')?<Img src={assetUrl(character_src)} style={{position:'absolute',left:'4%',bottom:'6%',height:'74%',objectFit:'contain'}}/>:null}
  {clips.filter(c=>!c.hidden).map(c=>{
    return <Sequence key={c.clip_id} from={Math.round(c.timeline_in*fps)} durationInFrames={Math.max(1,Math.round((c.timeline_out-c.timeline_in)*fps))}>
      <ClipView c={c} props={props}/>
    </Sequence>;
  })}
  {!props.phase2&&!clips.some(c=>c.track==='TEXT')?<div style={{position:'absolute',left:'48%',right:'5%',top:'36%',fontSize:62,fontWeight:800}}>{fallback_title}</div>:null}
</AbsoluteFill>;
};
