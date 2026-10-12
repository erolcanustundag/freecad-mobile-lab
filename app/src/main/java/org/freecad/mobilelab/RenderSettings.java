package org.freecad.mobilelab;
/** Immutable view/export settings. Geometry and exported CAD data stay independent. */
final class RenderSettings {
 static final int SHADED=0,STUDIO=1,ZEBRA=2,WIREFRAME=3;
 static final RenderSettings DEFAULT=new RenderSettings(SHADED,false,0,false);
 final int style;final boolean clip,transparent;final double clipZ;
 RenderSettings(int style,boolean clip,double z,boolean transparent){if(style<0||style>3||!Double.isFinite(z)||Math.abs(z)>1000000)throw new IllegalArgumentException("Invalid rendering settings");this.style=style;this.clip=clip;clipZ=z;this.transparent=transparent;}
 RenderSettings alpha(boolean a){return new RenderSettings(style,clip,clipZ,a);}
}
