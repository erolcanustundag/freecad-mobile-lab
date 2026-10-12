// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.*;
import android.widget.*;
import org.json.JSONArray;
/** Display genuine Part tessellation without loading the independent mobile CAD engine. */
final class PartPreview {
    static Dialog show(Activity activity,JSONArray coordinates)throws Exception{
        MeshFrame mesh=PartMesh.frame(coordinates);Dialog dialog=new Dialog(activity);LinearLayout root=new LinearLayout(activity);root.setOrientation(1);SoftwareCadView view=new SoftwareCadView(activity,message->new UiDialog(activity).setTitle("Part preview").setMessage(message).setPositiveButton("OK",null).show());view.setMesh(mesh,true);root.addView(view,new LinearLayout.LayoutParams(-1,0,1));Button close=new Button(activity);L10n.setText(close,"Close");close.setOnClickListener(v->dialog.dismiss());root.addView(close);dialog.setOnDismissListener(d->view.close());dialog.setContentView(root);dialog.show();dialog.getWindow().setLayout(-1,-1);return dialog;
    }
}
