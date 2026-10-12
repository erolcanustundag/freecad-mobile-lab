package org.freecad.mobilelab;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Bounded archive IO shared by project and FCStd import. */
final class ArchiveIO {
    static final long MAX_TOTAL=256L*1024*1024,MAX_SHAPE=128L*1024*1024,MAX_MANIFEST=1024*1024;
    static final class Budget {
        final long limit;
        long used;
        Budget(long limit){this.limit=limit;}
        void add(long bytes)throws IOException {
            if(bytes<0||bytes>limit-used)throw new IOException("Archive exceeds the mobile size limit");
            used+=bytes;
        }
    }
    static long copy(InputStream in,OutputStream out,long limit,Budget total)throws IOException {
        if(in==null||out==null)throw new IOException("File could not be opened");
        byte[] buffer=new byte[65536];long used=0;int n;
        while((n=in.read(buffer))!=-1) {
            if(n>limit-used)throw new IOException("File exceeds the mobile size limit");
            if(total!=null)total.add(n);out.write(buffer,0,n);used+=n;
        }
        return used;
    }
    static void deleteTree(File root) {
        File[] children=root.listFiles();if(children!=null)for(File f:children)deleteTree(f);
        root.delete();
    }
    static File unpackProject(File source,File cache)throws IOException {
        File dir=Files.createTempDirectory(cache.toPath(),"project-").toFile();boolean success=false;
        try {
            Set<String> seen=new HashSet<>();Budget budget=new Budget(MAX_TOTAL);
            try(ZipInputStream zip=new ZipInputStream(new FileInputStream(source))) {
                ZipEntry entry;
                while((entry=zip.getNextEntry())!=null) {
                    String name=entry.getName();
                    if(entry.isDirectory()||!name.matches("manifest\\.json|part-[0-9]+\\.(brep|stl)")||!seen.add(name)||seen.size()>501)
                        throw new IOException("Invalid or duplicate project entries");
                    long limit=name.equals("manifest.json")?MAX_MANIFEST:MAX_SHAPE;
                    if(entry.getSize()>limit)throw new IOException("Project entry is too large");
                    try(OutputStream out=new FileOutputStream(new File(dir,name))){copy(zip,out,limit,budget);}
                    zip.closeEntry();
                }
            }
            if(!seen.contains("manifest.json"))throw new IOException("Project manifest is missing");
            success=true;return dir;
        }finally{if(!success)deleteTree(dir);}
    }
    static void replaceFile(File temp,File destination)throws IOException {
        // The temp lives beside its destination, so no copy/truncate fallback is needed.
        try{Files.move(temp.toPath(),destination.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
        catch(AtomicMoveNotSupportedException e){Files.move(temp.toPath(),destination.toPath(),StandardCopyOption.REPLACE_EXISTING);}
    }
}
