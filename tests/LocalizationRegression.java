package org.freecad.mobilelab;
import java.util.*;
public final class LocalizationRegression {
    static int checks;
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);checks++;}
    public static void main(String[] args){
        check(LanguagePolicy.resolve("auto","tr-TR").equals("tr"),"Turkish region");
        check(LanguagePolicy.resolve("auto","de-CH").equals("de"),"German region");
        check(LanguagePolicy.resolve("auto","fr-FR").equals("en"),"Unsupported locale fallback");
        check(LanguagePolicy.resolve("auto","tr_TR").equals("tr"),"Legacy locale tag");
        check(LanguagePolicy.resolve("en","tr-TR").equals("en"),"Explicit English override");
        check(LanguagePolicy.resolve("tr","de-DE").equals("tr"),"Explicit Turkish override");
        check(LanguagePolicy.resolve("broken","de-DE").equals("de"),"Damaged preference fallback");
        check(LanguagePolicy.resourceName("Dil seçimi").matches("ui_[a-f0-9]{12}"),"Unicode resource identifier");
        Locale original=Locale.getDefault();
        try{for(Locale locale:new Locale[]{Locale.US,new Locale("tr","TR"),Locale.GERMANY}){
            Locale.setDefault(locale);
            for(String command:CommandLine.HELP.keySet())check(CommandLine.parse(command).name.equals(command),"Canonical command changed: "+command);
            String[][] aliases={{"Dil","Language"},{"DİL","Language"},{"Sprache","Language"},{"Kutu","Box"},{"KÜRE","Sphere"},{"Silindir","Cylinder"},{"YARDIM","Help"},{"YARDİM","Help"},{"AÇ","Open"},{"Kaydet","Save"},{"Geri","Undo"},{"Hilfe","Help"},{"Quader","Box"},{"Kugel","Sphere"}};
            for(String[] pair:aliases)check(CommandLine.parse(pair[0]).name.equals(pair[1]),"Locale alias: "+pair[0]);
            CommandLine.Request rename=CommandLine.parse("Rename \"İnci yüzüğüm\"");check(rename.args.get(0).equals("İnci yüzüğüm"),"Quoted Unicode model name changed");
            check(CommandLine.parse("Set ölçü 12.5").args.get(0).equals("ölçü"),"Variable name changed");
            check(CommandLine.parse("Kutu 20 10 4").args.equals(Arrays.asList("20","10","4")),"Numeric syntax changed");
            check(CommandLine.parse("Dil").ui(),"Language must be a UI command");
        }}finally{Locale.setDefault(original);}
        System.out.println("PASS: "+checks+" locale/fallback, canonical command, alias and Unicode data assertions");
    }
}
