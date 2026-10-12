// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.io.*;
import java.nio.charset.StandardCharsets;

public final class NativeTombstoneTest {
    private static byte[] varint(long value){ByteArrayOutputStream out=new ByteArrayOutputStream();while((value&~127L)!=0){out.write((int)value&127|128);value>>>=7;}out.write((int)value);return out.toByteArray();}
    private static byte[] join(byte[]... values)throws IOException {ByteArrayOutputStream out=new ByteArrayOutputStream();for(byte[] value:values)out.write(value);return out.toByteArray();}
    private static byte[] number(int field,long value)throws IOException{return join(varint(field*8),varint(value));}
    private static byte[] bytes(int field,byte[] value)throws IOException{return join(varint(field*8+2),varint(value.length),value);}
    private static byte[] text(int field,String value)throws IOException{return bytes(field,value.getBytes(StandardCharsets.UTF_8));}
    public static void main(String[] args)throws Exception {
        byte[] frame=join(number(1,0x1234),text(4,"NativeCad::create"),number(5,16),text(6,"libcad_mobile.so"),text(8,"test-build-id"));
        byte[] thread=join(number(1,77),text(2,"CAD worker"),bytes(4,frame));byte[] map=join(number(1,77),bytes(2,thread));
        byte[] signal=join(number(1,11),text(2,"SIGSEGV"),text(4,"SEGV_MAPERR"),number(9,0xdeadbeefL));
        byte[] root=join(number(6,77),bytes(10,signal),text(14,"test abort"),bytes(16,map),number(22,16384),number(1000,1));
        String out=NativeTombstone.describe(root);
        for(String expected:new String[]{"SIGSEGV","deadbeef","test abort","16384","Thread 77 CAD worker","libcad_mobile.so","NativeCad::create+16","test-build-id"})if(!out.contains(expected))throw new AssertionError(expected+" missing from "+out);
        for(byte[] bad:new byte[][]{{(byte)128},{18,20,1},{0},{11}}){try{NativeTombstone.describe(bad);throw new AssertionError("Malformed trace accepted");}catch(IOException expected){}}
        System.out.println("PASS: Android tombstone signal, abort, page size and crash-thread frames decoded; unknown fields skipped; truncated/invalid input rejected");
    }
}
