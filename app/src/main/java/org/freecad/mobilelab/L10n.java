// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.util.AtomicFile;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** Only presentation labels are translated. Stored names, expressions and command tokens stay intact. */
final class L10n {
    private static String choice="auto",language="en";private static Resources localized;
    private static final Map<String,Integer> ids=new HashMap<>();
    private static AtomicFile preference(Context c){return new AtomicFile(new File(c.getFilesDir(),"ui-language.txt"));}
    static synchronized void refresh(Context c){String next="auto";try{byte[] bytes=preference(c).readFully();if(bytes.length<16)next=LanguagePolicy.choice(new String(bytes,StandardCharsets.UTF_8).trim());}catch(IOException ignored){}String resolved=LanguagePolicy.resolve(next,Resources.getSystem().getConfiguration().getLocales().get(0).toLanguageTag());if(localized==null||!resolved.equals(language)){Configuration config=new Configuration(c.getResources().getConfiguration());config.setLocale(Locale.forLanguageTag(resolved));localized=c.createConfigurationContext(config).getResources();}choice=next;language=resolved;}
    static synchronized String language(Context c){if(localized==null)refresh(c);return language;}
    static synchronized String text(Context c,String source){if(source==null)return "";if(localized==null)refresh(c);Integer id=ids.get(source);if(id==null){id=localized.getIdentifier(LanguagePolicy.resourceName(source),"string",c.getPackageName());ids.put(source,id);}return id==0?source:localized.getString(id);}
    static String[] labels(Context c,String[] source){String[] result=source.clone();for(int i=0;i<result.length;i++)result[i]=text(c,source[i]);return result;}
    static void setText(TextView view,String source){view.setTag(R.id.l10n_text,source);view.setText(text(view.getContext(),source));}
    static void setHint(TextView view,String source){view.setTag(R.id.l10n_hint,source);view.setHint(text(view.getContext(),source));}
    static void update(View view){if(view instanceof TextView){TextView t=(TextView)view;Object value=view.getTag(R.id.l10n_text);if(value instanceof String)t.setText(text(view.getContext(),(String)value));value=view.getTag(R.id.l10n_hint);if(value instanceof String)t.setHint(text(view.getContext(),(String)value));}if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++)update(g.getChildAt(i));}view.invalidate();}
    static void picker(Activity a){refresh(a);String[] names={text(a,"Use phone language"),"English","Türkçe","Deutsch"};int selected=Arrays.asList(LanguagePolicy.CHOICES).indexOf(choice);new UiDialog(a).setTitle("Language").setSingleChoiceItems(names,selected,(dialog,index)->{AtomicFile file=preference(a);FileOutputStream stream=null;try{stream=file.startWrite();stream.write(LanguagePolicy.CHOICES[index].getBytes(StandardCharsets.UTF_8));file.finishWrite(stream);stream=null;refresh(a);dialog.dismiss();update(a.getWindow().getDecorView());}catch(IOException e){if(stream!=null)file.failWrite(stream);new UiDialog(a).setTitle("Language").setMessage("Could not save language preference").setPositiveButton("OK",null).show();}}).setNegativeButton("Cancel",null).show();}
    static String guide(Context c,String page){String lang=language(c),path="guide/"+page+".txt";try{if(!lang.equals("en")){String local="guide-"+lang+"/"+page+".txt";try(InputStream probe=c.getAssets().open(local)){path=local;}}}catch(IOException ignored){}return path;}
}
