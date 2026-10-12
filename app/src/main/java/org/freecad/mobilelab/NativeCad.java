package org.freecad.mobilelab;

final class NativeCad {
    static { System.loadLibrary("cad_mobile"); }
    static native void markGraphOwned(int id,boolean owned);
    static native int curve(String kind,double[] points,boolean closed,int replaceId);
    static native String curveData(int id);
    static native void beginPreview();
    static native void endPreview();
    static native void rebuild(int target,String kind,int[] inputs,double[] parameters);
    static native double[] samplePoint(int id,double[] fractions);
    static native String topology(int id);
    static native String surfaceData(int id);
    static native void surfacePole(int id,double[] parameters);
    static native String thickness(int id,double threshold);
    static native String curvature(int id);
    static native int model(String kind,int[] inputs,double[] parameters);
    static native int array(int id,String kind,int count,double[] parameters);
    static native int mirror(int id,double[] plane);
    static native void material(int id,double[] rgb);
    static native double distance(int first,int second);
    static native void writeWithTolerance(String path,String format,int selected,double tolerance);
    static native String analyze(int id,double draftDegrees);
    static native void surfaceMaterial(int id,double[] roughnessMetallic);
    static native float[] surfaceValues();
    static native float[] lines(int selected);
    static native int create(String type, double[] dimensions);
    static native void edit(int id, double[] dimensions);
    static native int operation(String type, int first, int second, double amount);
    static native void move(int id, double x, double y, double z);
    static native int duplicate(int id, double offsetX, double offsetY, double offsetZ);
    static native void scale(int id, double factor);
    static native void rotate(int id, double xDegrees, double yDegrees, double zDegrees);
    // Project BREP/STL files already contain the translated geometry.
    static native void restorePosition(int id, double[] position);
    static native void beginTransaction(boolean recordUndo);
    static native void commitTransaction();
    static native void rollbackTransaction();
    static native void visible(int id, boolean visible);
    static native void remove(int id);
    static native void clear();
    static native boolean undo();
    static native boolean redo();
    static native int pickFiltered(double[] ray,String filter);
    static native int[] pickElement(double[] ray,int kind);
    static native int pick(double[] ray);
    static native int drawing(double[] coordinates,int[] kinds);
    static native int textSolid(double[] xy,int[] contours,double depth);
    static native int arrayCurve(int source,int rail,int count,boolean orient);
    static native String getWorkspace();
    static native void setWorkspace(String state);
    static native void properties(int id,String name,String layer,boolean locked);
    static native String objects();
    static native float[] mesh(int selected);
    static native float[] meshAtDetail(int selected, int triangleBudget);
    static native void write(String path, String format, int selected);
    static native int read(String path, String format);
    static native String selfTest(String directory);
}
