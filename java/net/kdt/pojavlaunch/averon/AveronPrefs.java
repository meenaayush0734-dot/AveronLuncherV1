package net.kdt.pojavlaunch.averon;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;

/** Read Averon settings anywhere: AveronPrefs.ramMb(ctx) etc. */
public final class AveronPrefs {
    private AveronPrefs() {}
    private static SharedPreferences sp(Context c) {
        return PreferenceManager.getDefaultSharedPreferences(c);
    }
    public static int ramMb(Context c) { return sp(c).getInt("averon_ram_mb", 1536); }
    public static String renderer(Context c) { return sp(c).getString("averon_renderer", "gl4es"); }
    public static String javaVersion(Context c) { return sp(c).getString("averon_java", "17"); }
    public static int resScale(Context c) { return sp(c).getInt("averon_res_scale", 100); }
    public static String jvmArgs(Context c) { return sp(c).getString("averon_jvm_args", ""); }
    public static boolean fpsCounter(Context c) { return sp(c).getBoolean("averon_fps_counter", false); }
    public static boolean showLogs(Context c) { return sp(c).getBoolean("averon_show_logs", false); }
    public static boolean keepScreenOn(Context c) { return sp(c).getBoolean("averon_keep_screen_on", true); }
}
