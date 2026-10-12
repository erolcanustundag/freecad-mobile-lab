package org.freecad.mobilelab;
/** Bounded Cook-Torrance/GGX direct-light preview with a simple studio fill. */
final class StudioLighting {
 static float[] color(double nx,double ny,double nz,double vx,double vy,double vz,float[] base,double rough,double metal){
  double length=Math.sqrt(vx*vx+vy*vy+vz*vz);if(length<1e-12){vx=0;vy=0;vz=1;}else{vx/=length;vy/=length;vz/=length;}
  double lx=.3/Math.sqrt(1.58),ly=.7/Math.sqrt(1.58),lz=1/Math.sqrt(1.58),hx=lx+vx,hy=ly+vy,hz=lz+vz,hd=Math.sqrt(hx*hx+hy*hy+hz*hz);if(hd<1e-12)hd=1;hx/=hd;hy/=hd;hz/=hd;
  double nl=Math.max(0,nx*lx+ny*ly+nz*lz),nv=Math.max(.001,nx*vx+ny*vy+nz*vz),nh=Math.max(0,nx*hx+ny*hy+nz*hz),vh=Math.max(0,vx*hx+vy*hy+vz*hz);rough=Math.max(.04,Math.min(1,rough));metal=Math.max(0,Math.min(1,metal));double a=rough*rough,a2=a*a,d=nh*nh*(a2-1)+1,distribution=a2/(Math.PI*d*d),k=(rough+1)*(rough+1)/8,geometry=nv/(nv*(1-k)+k)*nl/(nl*(1-k)+k),fresnel=Math.pow(1-vh,5),fill=Math.max(0,(-nx*.8-ny*.2+nz*.6)/Math.sqrt(1.04));float[] out=new float[3];
  for(int i=0;i<3;i++){double b=Math.pow(Math.max(0,Math.min(1,base[i])),2.2),f0=.04*(1-metal)+b*metal,f=f0+(1-f0)*fresnel,spec=distribution*geometry*f/Math.max(.001,4*nv*nl),diff=(1-f)*(1-metal)*b/Math.PI,light=3*(diff+spec)*nl+b*(.15+.18*fill)+f0*.15;out[i]=(float)Math.pow(light/(1+light),1/2.2);}return out;
 }
}
