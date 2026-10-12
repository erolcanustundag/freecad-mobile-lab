package org.freecad.mobilelab;

import java.io.*;
import java.util.*;
import java.util.zip.*;
import java.nio.file.Files;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

/** Imports saved Part BREP geometry from FCStd; does not emulate Python or a feature tree. */
final class FcstdImporter {
    private static Document xml(ZipFile zip,String name,ArchiveIO.Budget budget)throws Exception {
        ZipEntry entry=zip.getEntry(name);if(entry==null)return null;
        if(entry.getSize()>4*1024*1024)throw new IOException("FCStd XML is too large");
        byte[] raw;
        try(InputStream in=zip.getInputStream(entry);ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
            ArchiveIO.copy(in,bytes,4*1024*1024,budget);
            raw=bytes.toByteArray();
        }
        // FCStd XML is UTF-8 and has no DTD. Avoid Android DOM feature switches
        // that are unsupported by several framework parser implementations.
        String source=new String(raw,java.nio.charset.StandardCharsets.UTF_8);
        if(source.indexOf('\0')>=0||source.contains("<!DOCTYPE")||source.contains("<!ENTITY"))throw new IOException("Unsupported FCStd XML encoding or DTD");
        DocumentBuilderFactory f=DocumentBuilderFactory.newInstance();
        f.setExpandEntityReferences(false);
        return f.newDocumentBuilder().parse(new ByteArrayInputStream(raw));
    }
    static int read(File file,File cache)throws Exception {
        File staging=Files.createTempDirectory(cache.toPath(),"fcstd-").toFile();
        try(ZipFile zip=new ZipFile(file)) {
            ArchiveIO.Budget budget=new ArchiveIO.Budget(ArchiveIO.MAX_TOTAL);
            Set<String> entryNames=new HashSet<>();Enumeration<? extends ZipEntry> entries=zip.entries();
            while(entries.hasMoreElements())if(!entryNames.add(entries.nextElement().getName()))throw new IOException("Duplicate FCStd entries");
            Document document=xml(zip,"Document.xml",budget);if(document==null)throw new IOException("No FreeCAD Document.xml found");
            Map<String,Boolean> visible=new HashMap<>();Document gui=xml(zip,"GuiDocument.xml",budget);
            if(gui!=null){NodeList providers=gui.getElementsByTagName("ViewProvider");for(int i=0;i<providers.getLength();i++){Element provider=(Element)providers.item(i);NodeList properties=provider.getElementsByTagName("Property");for(int j=0;j<properties.getLength();j++){Element p=(Element)properties.item(j);if(p.getAttribute("name").equals("Visibility")){NodeList booleans=p.getElementsByTagName("Bool");if(booleans.getLength()>0){String value=((Element)booleans.item(0)).getAttribute("value");visible.put(provider.getAttribute("name"),!value.equals("false")&&!value.equals("0"));}}}}}
            Set<String> references=new LinkedHashSet<>();NodeList objects=document.getElementsByTagName("Object");
            for(int i=0;i<objects.getLength();i++){Element object=(Element)objects.item(i);if(Boolean.FALSE.equals(visible.get(object.getAttribute("name"))))continue;NodeList parts=object.getElementsByTagName("Part");for(int j=0;j<parts.getLength();j++){String ref=((Element)parts.item(j)).getAttribute("file");if(!ref.isEmpty())references.add(ref);if(references.size()>250)throw new IOException("FCStd exceeds 250 saved shapes");}}
            for(String ref:references){ZipEntry e=zip.getEntry(ref);if(e==null||e.isDirectory()||e.getSize()==0)throw new IOException("FCStd saved shape is missing: "+ref);if(e.getSize()>ArchiveIO.MAX_SHAPE)throw new IOException("FCStd saved shape is too large");}
            int last=0,count=0;
            for(String ref:references){ZipEntry e=zip.getEntry(ref);
                File local=new File(staging,"shape-"+(++count)+".brep");
                try(InputStream in=zip.getInputStream(e);OutputStream out=new FileOutputStream(local)){ArchiveIO.copy(in,out,ArchiveIO.MAX_SHAPE,budget);}
                last=NativeCad.read(local.getAbsolutePath(),"brep");local.delete();
            }
            if(last==0)throw new IOException("No supported visible saved Part BREP shapes found. This build imports stored geometry, not the desktop feature history or Python objects.");
            return last;
        }finally{ArchiveIO.deleteTree(staging);}
    }
}
