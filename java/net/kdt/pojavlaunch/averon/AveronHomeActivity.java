package net.kdt.pojavlaunch.averon;

import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONObject;

/** Averon home screen. Hook the TODO lines into PojavLauncher's real version list / launch code. */
public class AveronHomeActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(net.kdt.pojavlaunch.R.layout.averon_activity_home);
        TextView notice = findViewById(net.kdt.pojavlaunch.R.id.averonNotice);
        Button play = findViewById(net.kdt.pojavlaunch.R.id.averonPlay);
        Button adv = findViewById(net.kdt.pojavlaunch.R.id.averonAdvanced);
        View host = findViewById(net.kdt.pojavlaunch.R.id.averonFragmentHost);

        AveronApi.getConfig(cfg -> runOnUiThread(() -> {
            if (cfg != null && !cfg.optString("notice").isEmpty()) notice.setText(cfg.optString("notice"));
        }));

        adv.setOnClickListener(v -> getSupportFragmentManager().beginTransaction()
            .replace(net.kdt.pojavlaunch.R.id.averonFragmentHost, new AveronAdvancedFragment())
            .addToBackStack(null).commit());

        play.setOnClickListener(v -> {
            int ram = AveronPrefs.ramMb(this);
            String renderer = AveronPrefs.renderer(this);
            String java = AveronPrefs.javaVersion(this);
            String jvm = AveronPrefs.jvmArgs(this);
            // TODO: pass ram/renderer/java/jvm into Pojav's launch call, start the game.
            // TODO: on crash -> AveronApi.reportCrash(version, android.os.Build.MODEL, logText);
            Toast.makeText(this, "Launch hook not connected yet", Toast.LENGTH_SHORT).show();
        });
    }
}
