// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.Activity;
import android.os.Bundle;
abstract class LocalizedActivity extends Activity {
    @Override public void onCreate(Bundle state){L10n.refresh(this);super.onCreate(state);}
    @Override protected void onResume(){super.onResume();L10n.refresh(this);L10n.update(getWindow().getDecorView());}
}
