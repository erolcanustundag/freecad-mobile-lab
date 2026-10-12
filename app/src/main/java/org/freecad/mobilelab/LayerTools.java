// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.util.*;
import org.json.*;
final class LayerTools {
    static String[] names(JSONArray objects){TreeSet<String> names=new TreeSet<>();for(int i=0;i<objects.length();i++)names.add(objects.optJSONObject(i).optString("layer","Default"));return names.toArray(new String[0]);}
    static int apply(String layer,Boolean visible,Boolean locked)throws Exception{if(layer==null||layer.isEmpty()||layer.length()>128)throw new IllegalArgumentException("Enter a valid layer name");JSONArray objects=new JSONArray(NativeCad.objects());int count=0;for(int i=0;i<objects.length();i++){JSONObject o=objects.getJSONObject(i);if(!layer.equals(o.optString("layer","Default")))continue;int id=o.getInt("id");if(visible!=null)NativeCad.visible(id,visible);if(locked!=null)NativeCad.properties(id,o.optString("name",""),layer,locked);count++;}if(count==0)throw new IllegalArgumentException("No objects on layer: "+layer);return count;}
}
