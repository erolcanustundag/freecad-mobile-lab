package org.freecad.mobilelab;

import java.io.IOException;
import org.json.*;

/** Metadata migration is in memory; opening a legacy project never rewrites its source. */
final class ProjectSchema {
    static final int CURRENT=2;
    static JSONObject read(String text)throws Exception {
        JSONObject m=new JSONObject(text);int version=m.optInt("version");
        if(!m.optString("format").equals("FreeCADMobileLab")||!m.optString("units").equals("mm")||version<1||version>CURRENT)
            throw new IOException("Unsupported project format, version, or units");
        m.getJSONArray("objects");
        if(version==CURRENT) {
            if(m.optInt("minimumReader")!=CURRENT||m.optString("writer").isEmpty()||m.optString("writer").length()>80||!m.optString("geometryKernel").equals("OCCT-7.9.2"))
                throw new IOException("Unsupported project reader or geometry kernel");
            m.getJSONArray("features");
        } else {
            if(!m.has("features"))m.put("features",new JSONArray());
            m.put("minimumReader",CURRENT).put("writer","migrated-from-v1").put("geometryKernel","OCCT-7.9.2").put("version",CURRENT);
        }
        return m;
    }
    static JSONObject fresh(JSONArray objects)throws Exception {
        return new JSONObject().put("format","FreeCADMobileLab").put("version",CURRENT).put("minimumReader",CURRENT)
            .put("writer",ReleaseInfo.VERSION).put("geometryKernel","OCCT-7.9.2").put("units","mm").put("objects",objects);
    }
}
