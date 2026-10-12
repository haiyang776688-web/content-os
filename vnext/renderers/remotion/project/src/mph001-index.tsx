import React from 'react';
import {CalculateMetadataFunction, Composition, registerRoot} from 'remotion';
import {Renderer, VREProps} from './vre001/Renderer';

const defaults:VREProps={
  clips:[],fps:30,width:1920,height:1080,duration_frames:450,
  font_src:'PREVIEW-VGB001/font.otf',visual_mode:'MPH_001_GALLERY',
};

const calculateMetadata:CalculateMetadataFunction<VREProps>=({props})=>({
  durationInFrames:props.duration_frames,
  fps:props.fps,
  width:props.width,
  height:props.height,
});

const Root=()=> <Composition
  id="MPH001MotionPrimitiveGallery"
  component={Renderer}
  durationInFrames={450}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={defaults}
  calculateMetadata={calculateMetadata}
/>;

registerRoot(Root);
