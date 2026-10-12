// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.util.*;
import org.json.*;

/** Bounded scalar expressions. No scripts, reflection, filesystem or Python execution. */
final class Expressions {
    private static LinkedHashMap<String,String> variables=new LinkedHashMap<>();
    private static final Map<String,Double> CONSTANTS=new HashMap<>();
    static {CONSTANTS.put("pi",Math.PI);CONSTANTS.put("e",Math.E);CONSTANTS.put("mm",1.0);CONSTANTS.put("cm",10.0);CONSTANTS.put("m",1000.0);CONSTANTS.put("in",25.4);CONSTANTS.put("deg",Math.PI/180);}
    static double evaluate(String text){return evaluate(text,variables,new HashSet<String>(),0);}
    static double evaluateIn(String text,Map<String,String> extra){Map<String,String> values=new LinkedHashMap<>(variables);values.putAll(extra);return evaluate(text,values,new HashSet<String>(),0);}
    private static double evaluate(String text,Map<String,String> vars,Set<String> active,int depth){
        if(text==null||text.isEmpty()||text.length()>256||depth>32)throw new IllegalArgumentException("Expression is empty, too long or too deeply nested");
        return new Parser(text,vars,active,depth).parse();
    }
    static void set(String name,String expression){
        if(name==null||!name.matches("[A-Za-z][A-Za-z0-9_]{0,31}")||CONSTANTS.containsKey(name))throw new IllegalArgumentException("Variable needs a unique name, starting with a letter (up to 32 characters)");
        LinkedHashMap<String,String> next=new LinkedHashMap<>(variables);next.put(name,expression);validate(next);variables=next;
    }
    static void remove(String name){LinkedHashMap<String,String> next=new LinkedHashMap<>(variables);if(next.remove(name)==null)throw new IllegalArgumentException("Unknown variable: "+name);validate(next);variables=next;}
    static void reset(){variables=new LinkedHashMap<>();}
    private static void validate(Map<String,String> next){if(next.size()>64)throw new IllegalArgumentException("At most 64 document variables");for(Map.Entry<String,String> e:next.entrySet()){if(!e.getKey().matches("[A-Za-z][A-Za-z0-9_]{0,31}")||CONSTANTS.containsKey(e.getKey()))throw new IllegalArgumentException("Invalid variable name");evaluate(e.getValue(),next,new HashSet<String>(),0);}}
    static JSONObject json()throws Exception{JSONObject o=new JSONObject();for(Map.Entry<String,String> e:variables.entrySet())o.put(e.getKey(),e.getValue());return o;}
    static void load(JSONObject json)throws Exception{LinkedHashMap<String,String> next=new LinkedHashMap<>();if(json!=null){Iterator<String> keys=json.keys();while(keys.hasNext()){String name=keys.next();next.put(name,json.getString(name));}}validate(next);variables=next;}
    static void validateJson(JSONObject json)throws Exception{JSONObject old=json();try{load(json);}finally{load(old);}}
    static String report(){StringBuilder out=new StringBuilder("Scalar values. Length units: mm, cm, m, in. Trigonometry uses radians; 90deg converts to radians.\n\n");for(Map.Entry<String,String> e:variables.entrySet())out.append(e.getKey()).append(" = ").append(e.getValue()).append(" → ").append(String.format(Locale.US,"%.10g",evaluate(e.getValue()))).append('\n');if(variables.isEmpty())out.append("No variables. Try Set bore 18, then Ring bore 1.6 3.\n");out.append("\nCommands evaluate expressions once. Changing a variable does not yet regenerate existing geometry.");return out.toString();}
    private static double bounded(double value){if(!Double.isFinite(value)||Math.abs(value)>1e12)throw new IllegalArgumentException("Expression result must be finite and within +/- 1e12");return value;}
    private static final class Parser {
        final String text;final Map<String,String> vars;final Set<String> active;final int depth;int pos,steps,nesting;
        Parser(String text,Map<String,String> vars,Set<String> active,int depth){this.text=text;this.vars=vars;this.active=active;this.depth=depth;}
        double parse(){double value=sum();space();if(pos!=text.length())throw new IllegalArgumentException("Unexpected expression character at "+(pos+1));return bounded(value);}
        void space(){while(pos<text.length()&&Character.isWhitespace(text.charAt(pos)))pos++;}
        boolean take(char c){space();if(++steps>1024)throw new IllegalArgumentException("Expression is too complex");if(pos<text.length()&&text.charAt(pos)==c){pos++;return true;}return false;}
        double sum(){double x=product();while(true){if(take('+'))x=bounded(x+product());else if(take('-'))x=bounded(x-product());else return x;}}
        double product(){double x=unary();while(true){if(take('*'))x=bounded(x*unary());else if(take('/')){double y=unary();if(y==0)throw new IllegalArgumentException("Division by zero");x=bounded(x/y);}else if(take('%')){double y=unary();if(y==0)throw new IllegalArgumentException("Modulo by zero");x=bounded(x%y);}else return x;}}
        double unary(){if(++nesting>48)throw new IllegalArgumentException("Expression nesting is too deep");try{if(take('+'))return unary();if(take('-'))return bounded(-unary());double x=atom();if(take('^'))x=bounded(Math.pow(x,unary()));return x;}finally{nesting--;}}
        String name(){space();int begin=pos;while(pos<text.length()&&(Character.isLetterOrDigit(text.charAt(pos))||text.charAt(pos)=='_'))pos++;return text.substring(begin,pos);}
        double atom(){if(take('(')){double value=sum();if(!take(')'))throw new IllegalArgumentException("Missing closing parenthesis");return value;}space();if(pos==text.length())throw new IllegalArgumentException("Missing expression value");char c=text.charAt(pos);
            if(Character.isDigit(c)||c=='.'){int begin=pos;while(pos<text.length()&&(Character.isDigit(text.charAt(pos))||text.charAt(pos)=='.'))pos++;if(pos<text.length()&&(text.charAt(pos)=='e'||text.charAt(pos)=='E')&&pos+1<text.length()&&(Character.isDigit(text.charAt(pos+1))||text.charAt(pos+1)=='+'||text.charAt(pos+1)=='-')){pos++;if(pos<text.length()&&(text.charAt(pos)=='+'||text.charAt(pos)=='-'))pos++;while(pos<text.length()&&Character.isDigit(text.charAt(pos)))pos++;}double value;try{value=bounded(Double.parseDouble(text.substring(begin,pos)));}catch(NumberFormatException e){throw new IllegalArgumentException("Invalid expression number");}space();if(pos<text.length()&&Character.isLetter(text.charAt(pos))){String unit=name();if(!CONSTANTS.containsKey(unit)||unit.equals("pi")||unit.equals("e"))throw new IllegalArgumentException("Unknown unit: "+unit);value=bounded(value*CONSTANTS.get(unit));}return value;}
            if(Character.isLetter(c)){String id=name();if(take('(')){double value=sum();if(!take(')'))throw new IllegalArgumentException("Missing function parenthesis");switch(id){case "sqrt":value=Math.sqrt(value);break;case "abs":value=Math.abs(value);break;case "sin":value=Math.sin(value);break;case "cos":value=Math.cos(value);break;case "tan":value=Math.tan(value);break;case "floor":value=Math.floor(value);break;case "ceil":value=Math.ceil(value);break;case "round":value=Math.floor(value+.5);break;default:throw new IllegalArgumentException("Unknown function: "+id);}return bounded(value);}if(CONSTANTS.containsKey(id))return CONSTANTS.get(id);String definition=vars.get(id);if(definition==null)throw new IllegalArgumentException("Unknown variable: "+id);if(!active.add(id))throw new IllegalArgumentException("Variable dependency cycle: "+id);try{return evaluate(definition,vars,active,depth+1);}finally{active.remove(id);}}
            throw new IllegalArgumentException("Invalid expression character");
        }
    }
}
