import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Player,PlayerRef} from '@remotion/player';
import {scene,Props} from './Composition';
// Projection controls only. The Player's frame/audio clock owns playback.
const Monitor=()=>{
  const ref=useRef<PlayerRef>(null);
  const [props,setProps]=useState<Props|null>(null);
  const [safe,setSafe]=useState(false);
  const [zoom,setZoom]=useState('fit');
  const [size,setSize]=useState([window.innerWidth,window.innerHeight]);
  useEffect(()=>{const resize=()=>setSize([window.innerWidth,window.innerHeight]);window.addEventListener('resize',resize);return()=>window.removeEventListener('resize',resize)},[]);
  const send=(value:object)=>parent.postMessage({source:'CONTENT_OS_MONITOR',...value},location.origin);
  useEffect(()=>{
    const receive=(e:MessageEvent)=>{
      if(e.source!==parent||e.origin!==location.origin||e.data?.source!=='CONTENT_OS_TIMELINE')return;
      const d=e.data;
      if(d.type==='composition'){const p=structuredClone(d.props);for(const c of p.clips)if(c.asset_src)c.asset_src='/api/preview-assets/'+c.asset_src;for(const f of p.fonts??[])f.src='/api/preview-assets/'+f.src;if(p.character_src)p.character_src='/api/preview-assets/'+p.character_src;setProps(p);}
      if(d.type==='seek')ref.current?.seekTo(d.frame);
      if(d.type==='toggle')ref.current?.toggle();
      if(d.type==='pause')ref.current?.pause();
      if(d.type==='safe')setSafe(d.value);
      if(d.type==='zoom')setZoom(d.value);
    };
    const key=(e:KeyboardEvent)=>{if(e.code==='Space'){e.preventDefault();ref.current?.toggle()}};
    window.addEventListener('keydown',key);window.addEventListener('message',receive);send({type:'ready'});
    return()=>{window.removeEventListener('keydown',key);window.removeEventListener('message',receive)};
  },[]);
  useEffect(()=>{const p=ref.current;if(!p)return;
    const frame=(e:any)=>send({type:'frame',frame:e.detail.frame});
    const play=()=>send({type:'playing',value:true});const pause=()=>send({type:'playing',value:false});
    const error=(e:any)=>send({type:'error',message:String(e.detail.error)});
    p.addEventListener('frameupdate',frame);p.addEventListener('play',play);p.addEventListener('pause',pause);p.addEventListener('ended',pause);p.addEventListener('error',error);
    send({type:'loaded'});
    return()=>{p.removeEventListener('frameupdate',frame);p.removeEventListener('play',play);p.removeEventListener('pause',pause);p.removeEventListener('ended',pause);p.removeEventListener('error',error)};
  },[props]);
  return props?<div style={{position:'relative',width:zoom==='fit'?Math.min(size[0],size[1]*props.width/props.height):props.width*Number(zoom),margin:'auto'}}>
    <Player ref={ref} component={scene} inputProps={props} fps={props.fps} compositionWidth={props.width} compositionHeight={props.height} durationInFrames={props.duration_frames} controls={false} clickToPlay={false} spaceKeyToPlayOrPause={false} style={{width:'100%'}}/>
    {safe?<><div data-safe-area="action" style={{position:'absolute',inset:'5%',border:'1px dashed #eee',pointerEvents:'none'}}/><div data-safe-area="title" style={{position:'absolute',inset:'10%',border:'1px dashed #ffc800',pointerEvents:'none'}}/></>:null}
  </div>:null;
};
createRoot(document.getElementById('monitor-root')!).render(<Monitor/>);
