import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Renderer, VREProps} from './vre001/Renderer';

const defaults:VREProps={clips:[],fps:30,width:1920,height:1080,duration_frames:574,font_src:'PREVIEW-VRE001/font.otf',visual_mode:'BRAND_BALANCED'};

const Root=()=> <Composition
  id="VRE001F2Reproduction"
  component={Renderer}
  durationInFrames={574}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={defaults}
/>;

registerRoot(Root);
