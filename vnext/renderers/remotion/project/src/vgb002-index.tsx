import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Film, FPS, FRAMES} from './vgb001/shared';
import {F1} from './vgb002/F1';
import {F2} from './vgb002/F2';

const EvidenceHeavy = () => <Film><F1 /></Film>;
const BrandBalanced = () => <Film><F2 /></Film>;

const Root = () => <>
  <Composition id="VGB002F1" component={EvidenceHeavy} durationInFrames={FRAMES} fps={FPS} width={1920} height={1080} />
  <Composition id="VGB002F2" component={BrandBalanced} durationInFrames={FRAMES} fps={FPS} width={1920} height={1080} />
</>;

registerRoot(Root);
