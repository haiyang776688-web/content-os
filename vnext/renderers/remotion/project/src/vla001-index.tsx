import React from 'react';
import {CalculateMetadataFunction, Composition, registerRoot} from 'remotion';
import {Renderer, VREProps} from './vre001/Renderer';

const defaults:VREProps={
  clips:[],fps:30,width:1920,height:1080,duration_frames:900,
  font_src:'PREVIEW-VRE001/font.otf',visual_mode:'BRAND_BALANCED',
};

const calculateMetadata:CalculateMetadataFunction<VREProps>=({props})=>({
  durationInFrames:props.duration_frames,
  fps:props.fps,
  width:props.width,
  height:props.height,
});

const Root=()=> <Composition
  id="VLA001Storyboard"
  component={Renderer}
  durationInFrames={900}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={defaults}
  calculateMetadata={calculateMetadata}
/>;

registerRoot(Root);
