import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {scene,defaults} from './Composition';
const Root:React.FC=()=> <Composition id="ContentOSPreview" component={scene} width={defaults.width} height={defaults.height} fps={defaults.fps} durationInFrames={defaults.duration_frames} defaultProps={defaults} calculateMetadata={({props})=>({durationInFrames:props.duration_frames,width:props.width,height:props.height,fps:props.fps})}/>;
registerRoot(Root);
