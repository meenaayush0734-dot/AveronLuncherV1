package net.kdt.pojavlaunch.averon;

import android.os.Bundle;
import androidx.preference.PreferenceFragmentCompat;

/** Averon advanced settings screen. Open it from your settings menu. */
public class AveronAdvancedFragment extends PreferenceFragmentCompat {
    @Override
    public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
        setPreferencesFromResource(
            net.kdt.pojavlaunch.R.xml.averon_preferences, rootKey);
    }
}
