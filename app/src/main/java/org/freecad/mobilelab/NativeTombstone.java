// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Reads crash signal and frames from Android's public tombstone.proto schema. */
final class NativeTombstone {
    private static final class Message {
        final Map<Integer,Long> numbers=new HashMap<>();
        final Map<Integer,List<byte[]>> bytes=new HashMap<>();
        Message(byte[] data)throws IOException {
            if(data==null||data.length>4*1024*1024)throw new IOException("Invalid native trace size");
            Reader r=new Reader(data);int count=0;
            while(r.at<data.length) {
                if(++count>100000)throw new IOException("Too many native trace fields");
                long tag=r.varint();int field=(int)(tag>>>3),wire=(int)(tag&7);if(field<=0)throw new IOException("Invalid protobuf field");
                if(wire==0)numbers.put(field,r.varint());
                else if(wire==1)r.skip(8);
                else if(wire==5)r.skip(4);
                else if(wire==2){long n=r.varint();if(n<0||n>data.length-r.at)throw new IOException("Truncated native trace");byte[] value=Arrays.copyOfRange(data,r.at,r.at+(int)n);r.at+=(int)n;bytes.computeIfAbsent(field,k->new ArrayList<>()).add(value);}
                else throw new IOException("Unsupported native trace wire type");
            }
        }
        long number(int field){Long value=numbers.get(field);return value==null?0:value;}
        List<byte[]> values(int field){List<byte[]> value=bytes.get(field);return value==null?Collections.emptyList():value;}
        byte[] first(int field){List<byte[]> value=values(field);return value.isEmpty()?new byte[0]:value.get(0);}
        String text(int field){byte[] value=first(field);return new String(value,0,Math.min(value.length,4096),StandardCharsets.UTF_8);}
    }
    private static final class Reader {
        final byte[] bytes;int at;
        Reader(byte[] bytes){this.bytes=bytes;}
        long varint()throws IOException {long n=0;for(int shift=0;shift<64;shift+=7){if(at>=bytes.length)throw new IOException("Truncated protobuf integer");int b=bytes[at++]&255;n|=(long)(b&127)<<shift;if((b&128)==0)return n;}throw new IOException("Invalid protobuf integer");}
        void skip(int n)throws IOException {if(n>bytes.length-at)throw new IOException("Truncated native trace");at+=n;}
    }
    static String describe(byte[] bytes)throws IOException {
        Message root=new Message(bytes),signal=new Message(root.first(10));StringBuilder out=new StringBuilder();
        out.append("Native signal ").append(signal.number(1)).append(' ').append(signal.text(2)).append(' ').append(signal.text(4)).append("\nFault address: 0x").append(Long.toHexString(signal.number(9))).append('\n');
        if(!root.text(14).isEmpty())out.append("Abort: ").append(root.text(14)).append('\n');
        if(root.number(22)>0)out.append("Memory page size: ").append(root.number(22)).append('\n');
        for(byte[] cause:root.values(15))out.append("Cause: ").append(new Message(cause).text(1)).append('\n');
        long tid=root.number(6);int printed=0;
        for(int field:new int[]{16,25})for(byte[] entry:root.values(field)) {
            Message map=new Message(entry);if(tid!=0&&map.number(1)!=tid)continue;Message thread=new Message(map.first(2));
            if(printed++>=2)break;out.append("Thread ").append(map.number(1)).append(' ').append(thread.text(2)).append(field==25?" (guest)":"").append('\n');int index=0;
            for(byte[] raw:thread.values(4)){if(index>=64)break;Message f=new Message(raw);out.append('#').append(index++).append(" pc 0x").append(Long.toHexString(f.number(1))).append(' ').append(f.text(6));if(!f.text(4).isEmpty())out.append(" (").append(f.text(4)).append('+').append(f.number(5)).append(')');if(!f.text(8).isEmpty())out.append(" [build ").append(f.text(8)).append(']');out.append('\n');}
        }
        return out.toString();
    }
}
