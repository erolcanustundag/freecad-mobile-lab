// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
/** Fixed menus use L10n.labels explicitly so user object names are never translated. */
final class UiDialog extends AlertDialog.Builder {
    private final Context context;UiDialog(Context c){super(c);context=c;}
    @Override public UiDialog setTitle(CharSequence v){super.setTitle(L10n.text(context,v==null?null:v.toString()));return this;}
    @Override public UiDialog setMessage(CharSequence v){super.setMessage(L10n.text(context,v==null?null:v.toString()));return this;}
    @Override public UiDialog setPositiveButton(CharSequence v,DialogInterface.OnClickListener a){super.setPositiveButton(L10n.text(context,v.toString()),a);return this;}
    @Override public UiDialog setNegativeButton(CharSequence v,DialogInterface.OnClickListener a){super.setNegativeButton(L10n.text(context,v.toString()),a);return this;}
    @Override public UiDialog setNeutralButton(CharSequence v,DialogInterface.OnClickListener a){super.setNeutralButton(L10n.text(context,v.toString()),a);return this;}
}
