// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import android.app.*;
import android.content.*;
import android.net.Uri;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.concurrent.*;

/** Lightweight launcher/recovery UI. It never loads CAD libraries or opens an EGL context. */
public final class StartupActivity extends LocalizedActivity {
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView message,details;
    private Button open;
    private boolean opened,destroyed,previousCrash;
    private String report="Reading the previous session…";
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);Diagnostics.stage(this,"Recovery screen created");
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(28,28,28,20);root.setBackgroundColor(0xff111820);
        root.setOnApplyWindowInsetsListener((v,i)->{root.setPadding(28+i.getSystemWindowInsetLeft(),28+i.getSystemWindowInsetTop(),28+i.getSystemWindowInsetRight(),20+i.getSystemWindowInsetBottom());return i;});
        TextView title=text("FREECAD / MOBILE LAB",22);root.addView(title);root.addView(text(ReleaseInfo.VERSION+" · native CAD · software 3D",14));
        message=text("Checking the previous session…",16);message.setPadding(0,24,0,16);root.addView(message);
        open=button("Open CAD workspace",()->launch(false,previousCrash));open.setEnabled(false);root.addView(open);
        root.addView(button("Language",()->L10n.picker(this)));
        root.addView(button("Open saved workspace",()->launch(false,false)));
        root.addView(button("Start empty workspace",()->launch(false,true)));
        root.addView(button("Try OpenGL renderer",()->launch(true,false)));
        root.addView(button("FreeCAD document lab",()->startActivity(new Intent(this,CoreDocumentActivity.class))));
        root.addView(button("Copy crash report",()->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("FreeCAD crash report",report));Toast.makeText(this,L10n.text(this,"Crash report copied"),Toast.LENGTH_SHORT).show();}));
        root.addView(button("Save crash report (.zip)",()->{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/zip");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_TITLE,"FreeCAD-crash-report.zip");startActivityForResult(i,40);}));
        details=text(report,12);details.setTextIsSelectable(true);root.addView(details);ScrollView scroll=new ScrollView(this);scroll.addView(root);setContentView(scroll);
        refresh(state==null&&!getIntent().getBooleanExtra("diagnostics_only",false));
    }
    private TextView text(String value,int size){TextView t=new TextView(this);L10n.setText(t,value);t.setTextColor(0xffedf3f8);t.setTextSize(size);return t;}
    private Button button(String value,Runnable action){Button b=new Button(this);L10n.setText(b,value);b.setAllCaps(false);b.setOnClickListener(v->action.run());return b;}
    private void launch(boolean gpu,boolean empty){opened=true;Intent i=new Intent(this,MainActivity.class);i.putExtra("renderer",gpu?"gles":"software");i.putExtra("empty_workspace",empty);startActivity(i);}
    private void refresh(boolean auto) {
        worker.execute(()->{
            boolean bad=Diagnostics.hadStartupFailure(this)||Diagnostics.recentSystemCrash(this);String next=Diagnostics.report(this,false);
            runOnUiThread(()->{if(destroyed)return;previousCrash=bad;report=next;details.setText(report);open.setEnabled(true);L10n.setText(open,bad?"Start empty CAD workspace":"Open CAD workspace");L10n.setText(message,bad?"A previous session crashed. Start an empty workspace with software 3D; the saved model will be kept as a recovery copy. Or copy the report below.":"Ready. Software 3D avoids OpenGL at startup.");if(auto&&!bad)launch(false,false);});
        });
    }
    @Override protected void onResume(){super.onResume();if(opened)refresh(false);}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);refresh(false);}
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);if(request!=40||result!=RESULT_OK||data==null||data.getData()==null)return;Uri destination=data.getData();
        worker.execute(()->{try(OutputStream out=getContentResolver().openOutputStream(destination,"wt")){if(out==null)throw new IOException("Cannot open destination");Diagnostics.export(this,out);runOnUiThread(()->{if(!destroyed)Toast.makeText(this,L10n.text(this,"Crash report saved"),Toast.LENGTH_LONG).show();});}catch(Exception e){runOnUiThread(()->{if(!destroyed)new UiDialog(this).setTitle("Report export").setMessage(e.toString()).setPositiveButton("OK",null).show();});}});
    }
    @Override protected void onDestroy(){destroyed=true;worker.shutdown();super.onDestroy();}
}
