package org.freecad.mobilelab;
import java.util.*;
/** Parameterised native templates, also used by commands and project validation. */
final class JewelleryCatalog {
    static final Map<String,String[]> LABELS=new LinkedHashMap<>();static final Map<String,double[]> DEFAULTS=new LinkedHashMap<>();
    static {entry("Oval bezel",new String[]{"Stone width","Stone depth","Wall","Height","Seat depth"},new double[]{8,6,.6,3,1});entry("Rectangle bezel",new String[]{"Stone width","Stone depth","Wall","Height","Seat depth"},new double[]{8,6,.6,3,1});entry("Cushion bezel",new String[]{"Stone width","Stone depth","Wall","Height","Seat depth","Stone corner radius"},new double[]{8,6,.6,3,1,1});entry("Oval prongs",new String[]{"Stone width","Stone depth","Gallery wall","Height","Seat depth","Prong count","Prong diameter"},new double[]{8,6,.6,4,2,6,.9});entry("Comfort ring",new String[]{"Inner diameter","Wall","Band width","Inner edge bevel"},new double[]{18,1.6,3,.4});entry("Signet ring",new String[]{"Inner diameter","Wall","Band width","Face width X","Face height Z","Face thickness Y"},new double[]{18,1.6,3,10,8,2});entry("Pendant frame",new String[]{"Outer width","Outer height","Frame wall","Thickness","Bail outer radius"},new double[]{18,30,1.2,1.5,2.5});entry("Bangle",new String[]{"Inner width","Inner depth","Wall","Band width"},new double[]{60,50,2,4});}
    static void entry(String name,String[] labels,double[] values){LABELS.put(name,labels);DEFAULTS.put(name,values);}
    static int dimensions(String type){double[] p=DEFAULTS.get(type);return p==null?0:p.length;}
    static double mass(double cubicMillimetres,double density){if(!Double.isFinite(cubicMillimetres)||cubicMillimetres<=0||!Double.isFinite(density)||density<=0||density>30)throw new IllegalArgumentException("Enter a positive solid volume and density between 0 and 30 g/cm³");return cubicMillimetres*density/1000;}
}
