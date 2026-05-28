package com.sakurakugu.personal_system;

import android.os.Bundle;
import android.webkit.WebView;
import com.sakurakugu.personal_system.plugins.PhoneUsagePlugin;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(PhoneUsagePlugin.class);
        super.onCreate(savedInstanceState);
        配置链接长按行为();
    }

    private void 配置链接长按行为() {
        if (getBridge() == null || getBridge().getWebView() == null) {
            return;
        }

        WebView webView = getBridge().getWebView();
        webView.setHapticFeedbackEnabled(false);
        webView.setOnLongClickListener(view -> {
            WebView.HitTestResult 命中结果 = webView.getHitTestResult();
            if (命中结果 == null) {
                return false;
            }

            int 类型 = 命中结果.getType();
            return 类型 == WebView.HitTestResult.SRC_ANCHOR_TYPE
                || 类型 == WebView.HitTestResult.SRC_IMAGE_ANCHOR_TYPE;
        });
    }
}
