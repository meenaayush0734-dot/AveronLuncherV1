package net.kdt.pojavlaunch.averon;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

/** Talks to the Averon admin backend. Set BASE_URL to your deployed HTTPS URL. */
public final class AveronApi {
    public static final String BASE_URL = "https://YOUR-BACKEND-URL";
    public interface Callback { void done(JSONObject result); }

    public static void getConfig(Callback cb) {
        new Thread(() -> {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(BASE_URL + "/api/config").openConnection();
                c.setConnectTimeout(6000); c.setReadTimeout(6000);
                java.util.Scanner s = new java.util.Scanner(c.getInputStream()).useDelimiter("\\A");
                cb.done(new JSONObject(s.hasNext() ? s.next() : "{}"));
            } catch (Exception e) { cb.done(null); }
        }).start();
    }

    public static void post(String path, JSONObject body) {
        new Thread(() -> {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(BASE_URL + path).openConnection();
                c.setRequestMethod("POST"); c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/json");
                c.setConnectTimeout(6000); c.setReadTimeout(6000);
                try (OutputStream o = c.getOutputStream()) { o.write(body.toString().getBytes("UTF-8")); }
                c.getResponseCode();
            } catch (Exception ignored) {}
        }).start();
    }

    public static void reportCrash(String version, String device, String log) {
        try { post("/api/crash", new JSONObject().put("version", version).put("device", device).put("log", log)); }
        catch (Exception ignored) {}
    }
    public static void reportDownload(String mcVersion) {
        try { post("/api/download", new JSONObject().put("mc_version", mcVersion)); } catch (Exception ignored) {}
    }
}
