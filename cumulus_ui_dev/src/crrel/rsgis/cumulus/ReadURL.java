package crrel.rsgis.cumulus;

import java.io.*;
import java.net.*;


public class ReadURL {
    
    public static void readURL(String aURL){
        try {
            URL u = new URL(aURL);
            URLConnection uc = u.openConnection();
            InputStream is = uc.getInputStream();
            BufferedReader br = new BufferedReader(
                    new InputStreamReader(is));
            String s = null;
            while ((s = br.readLine()) != null) {
                System.out.println(s);
            }
            br.close();
        } catch (Exception e){
            System.out.println("Error occured: " + e);
        }
    }
    
    public static void main(String[] args) {
        readURL("https://api.rsgis.dev/development/cumulus/basins");
        readURL("https://api.rsgis.dev/development/cumulus/products");
    }
}