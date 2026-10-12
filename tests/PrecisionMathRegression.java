// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.util.*;
import org.json.*;
public final class PrecisionMathRegression {
    static int checks;
    static void near(double actual,double expected,double eps){checks++;if(!Double.isFinite(actual)||Math.abs(actual-expected)>eps)throw new AssertionError(actual+" expected "+expected);}
    static void check(boolean yes){checks++;if(!yes)throw new AssertionError("Check "+checks);}
    interface Action{void run()throws Exception;}
    static void reject(Action action)throws Exception{checks++;try{action.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("Expected rejection");}
    static double[] referenceEuler(double[] e,double[] v){double x=Math.toRadians(e[0]),y=Math.toRadians(e[1]),z=Math.toRadians(e[2]);double[] a={v[0],Math.cos(x)*v[1]-Math.sin(x)*v[2],Math.sin(x)*v[1]+Math.cos(x)*v[2]},b={Math.cos(y)*a[0]+Math.sin(y)*a[2],a[1],-Math.sin(y)*a[0]+Math.cos(y)*a[2]};return new double[]{Math.cos(z)*b[0]-Math.sin(z)*b[1],Math.sin(z)*b[0]+Math.cos(z)*b[1],b[2]};}
    public static void main(String[] args)throws Exception{
        Expressions.reset();near(Expressions.evaluate("2+3*4"),14,0);near(Expressions.evaluate("2^3^2"),512,0);near(Expressions.evaluate("-2^2"),-4,0);near(Expressions.evaluate("(-2)^2"),4,0);near(Expressions.evaluate("25.4mm/1in"),1,1e-12);near(Expressions.evaluate("2cm+3mm"),23,1e-12);near(Expressions.evaluate("1e-3"),.001,1e-12);near(Expressions.evaluate("sin(90deg)"),1,1e-12);near(Expressions.evaluate("sqrt(81)+floor(2.9)"),11,0);
        Expressions.set("bore","18");Expressions.set("outer","bore+2*1.6");near(Expressions.evaluate("outer"),21.2,1e-12);Expressions.set("bore","20");near(Expressions.evaluate("outer"),23.2,1e-12);JSONObject saved=Expressions.json();Expressions.reset();Expressions.load(saved);near(Expressions.evaluate("outer"),23.2,1e-12);
        reject(()->Expressions.set("bore","outer"));near(Expressions.evaluate("bore"),20,0);reject(()->Expressions.remove("bore"));near(Expressions.evaluate("bore"),20,0);reject(()->Expressions.load(new JSONObject().put("x","y").put("y","x")));near(Expressions.evaluate("bore"),20,0);
        for(String bad:new String[]{"1/0","sqrt(-1)","1e1000","foo(2)","1;2","2(3)","2**3","2xyz","pi(0)","(2+3","2+","NaN","1+java.lang.Runtime"})reject(()->Expressions.evaluate(bad));reject(()->Expressions.set("pi","3"));reject(()->Expressions.evaluate(String.join("",Collections.nCopies(64,"("))+"1"+String.join("",Collections.nCopies(64,")"))));
        Random r=new Random(2244);for(int i=0;i<1000;i++){double x=r.nextInt(80)-40,y=r.nextInt(80)-40;near(Expressions.evaluate("("+x+"+"+y+")*2"),(x+y)*2,1e-9);}
        near(PrecisionTools.angle(new double[]{1,0,0,0,0,0,0,1,0}),90,1e-12);near(PrecisionTools.angle(new double[]{1,0,0,0,0,0,-1,0,0}),180,1e-12);near(PrecisionTools.length(3,4,12),13,1e-12);reject(()->PrecisionTools.angle(new double[9]));reject(()->PrecisionTools.matrix(0,0,0,90));
        for(int i=0;i<1000;i++){double[] m=PrecisionTools.matrix(r.nextDouble()-.5,r.nextDouble()-.5,r.nextDouble()-.5,r.nextDouble()*720-360),v={r.nextDouble()*10,r.nextDouble()*10,r.nextDouble()*10},rotated=PrecisionTools.apply(m,v),fromEuler=referenceEuler(PrecisionTools.euler(m),v);for(int k=0;k<3;k++)near(fromEuler[k],rotated[k],1e-7);near(PrecisionTools.length(rotated[0],rotated[1],rotated[2]),PrecisionTools.length(v[0],v[1],v[2]),1e-8);}
        for(int degrees:new int[]{-90,90}){double[] m=PrecisionTools.matrix(0,1,0,degrees),v={2,3,4},actual=referenceEuler(PrecisionTools.euler(m),v),expected=PrecisionTools.apply(m,v);for(int k=0;k<3;k++)near(actual[k],expected[k],1e-8);}
        for(String view:new String[]{"Top","Bottom","Front","Back","Right","Left"}){float[] angles=CameraMath.preset(view);int[] faces=ViewCubeMath.visible(angles[0],angles[1]);check(faces.length==1);check(ViewCubeMath.NAMES[faces[0]].equals(view));check(ViewCubeMath.hit(angles[0],angles[1],0,0)==faces[0]);}
        for(int i=0;i<500;i++){float yaw=r.nextFloat()*360,pitch=r.nextFloat()*360;int[] faces=ViewCubeMath.visible(yaw,pitch);check(faces.length>=1&&faces.length<=3);for(int face:faces){double[] n=ViewCubeMath.project(ViewCubeMath.NORMALS[face],yaw,pitch);check(ViewCubeMath.hit(yaw,pitch,n[0],n[1])==face);double[] back=CameraMath.inverse(yaw,pitch,n[0],n[1],n[2]);for(int k=0;k<3;k++)near(back[k],ViewCubeMath.NORMALS[face][k],1e-9);}}
        System.out.println("PASS: "+checks+" precision math assertions (expressions, variables, units, rejection, independent pivot rotation, cube projection/hits)");
    }
}
