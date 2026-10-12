// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.util.Locale;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
final class LanguagePolicy {
    static final String[] CHOICES={"auto","en","tr","de"};
    static boolean supported(String tag){return "en".equals(tag)||"tr".equals(tag)||"de".equals(tag);}
    static String choice(String value){return value!=null&&(value.equals("auto")||supported(value))?value:"auto";}
    static String resolve(String selected,String systemTag){selected=choice(selected);if(!selected.equals("auto"))return selected;String language=Locale.forLanguageTag(systemTag==null?"":systemTag.replace('_','-')).getLanguage();return supported(language)?language:"en";}
    static String resourceName(String source){try{byte[] digest=MessageDigest.getInstance("SHA-1").digest(source.getBytes(StandardCharsets.UTF_8));StringBuilder b=new StringBuilder("ui_");for(int i=0;i<6;i++){int v=digest[i]&255;b.append(Character.forDigit(v>>>4,16)).append(Character.forDigit(v&15,16));}return b.toString();}catch(Exception e){throw new IllegalStateException(e);}}
}
