// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Typeface;
import android.widget.*;
import android.text.TextUtils;
import java.util.*;
import java.util.function.Consumer;
import org.json.*;

/** Bounded worksheet grid. State is read and committed on the serialized CAD worker. */
final class WorksheetEditor {
    interface Commit{void apply(String address,String source,Consumer<JSONObject> refresh);}
    static void show(Context context,JSONObject state,JSONObject display,Commit commit,Runnable csvImport,Runnable csvExport){
        LinearLayout panel=new LinearLayout(context);panel.setOrientation(LinearLayout.VERTICAL);int pad=(int)(12*context.getResources().getDisplayMetrics().density);panel.setPadding(pad,pad,pad,pad);
        TextView info=new TextView(context);L10n.setText(info,"A1:H32 · tap a cell to edit. Formulas start with = and can use cells or document variables. Geometry uses evaluated snapshots.");panel.addView(info);
        TableLayout table=new TableLayout(context);Map<String,Button> buttons=new HashMap<>();final JSONObject[] values={state};TableRow header=new TableRow(context);TextView corner=new TextView(context);corner.setText("  #  ");header.addView(corner);for(int col=0;col<Worksheet.COLS;col++){TextView label=new TextView(context);label.setText("   "+(char)('A'+col));label.setTypeface(null,Typeface.BOLD);header.addView(label,new TableRow.LayoutParams(pad*8,-2));}table.addView(header);
        Consumer<JSONObject> update=shown->{for(Map.Entry<String,Button> entry:buttons.entrySet()){String address=entry.getKey(),text=shown.optString(address,"");Button b=entry.getValue();b.setText(text.startsWith("#ERR")?"#ERR":text);b.setContentDescription(address+": "+text);}};
        for(int row=1;row<=Worksheet.ROWS;row++){TableRow tr=new TableRow(context);TextView label=new TextView(context);label.setText(String.valueOf(row));tr.addView(label);for(int col=0;col<Worksheet.COLS;col++){final String address=""+(char)('A'+col)+row;Button button=new Button(context);button.setAllCaps(false);button.setTextSize(11);button.setSingleLine(true);button.setEllipsize(TextUtils.TruncateAt.END);buttons.put(address,button);tr.addView(button,new TableRow.LayoutParams(pad*8,pad*4));button.setOnClickListener(v->{EditText input=new EditText(context);input.setText(values[0].optString(address,""));L10n.setHint(input,"Number, text, or =formula");new UiDialog(context).setTitle("Cell "+address).setView(input).setNegativeButton("Cancel",null).setPositiveButton("Apply",(d,w)->{String source=input.getText().toString();try{Worksheet.checkValue(source);commit.apply(address,source,shown->{try{if(source.isEmpty())values[0].remove(address);else values[0].put(address,source);update.accept(shown);}catch(Exception e){new UiDialog(context).setMessage(e.getMessage()).setPositiveButton("Close",null).show();}});}catch(Exception e){new UiDialog(context).setMessage(e.getMessage()).setPositiveButton("Close",null).show();}}).show();});}table.addView(tr);}
        update.accept(display);HorizontalScrollView horizontal=new HorizontalScrollView(context);horizontal.addView(table);ScrollView vertical=new ScrollView(context);vertical.addView(horizontal);panel.addView(vertical,new LinearLayout.LayoutParams(-1,pad*24));
        AlertDialog dialog=new UiDialog(context).setTitle("Mobile spreadsheet").setView(panel).setNegativeButton("Close",null).setNeutralButton("Import CSV",(d,w)->csvImport.run()).setPositiveButton("Export CSV",(d,w)->csvExport.run()).create();dialog.show();
    }
}
