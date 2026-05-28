package com.sakurakugu.personal_system.plugins;

import android.app.AppOpsManager;
import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.content.Intent;
import android.os.Process;
import android.provider.Settings;
import android.util.Log;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.PluginMethod;

@CapacitorPlugin(name = "PhoneUsage")
public class PhoneUsagePlugin extends Plugin {
    private static final String 日志标签 = "PhoneUsagePlugin";

    @PluginMethod
    public void checkUsageAccess(PluginCall call) {
        boolean 已授权 = 是否已授权使用情况访问();
        Log.i(日志标签, "使用情况访问权限状态: " + 已授权);

        JSObject 结果 = new JSObject();
        结果.put("granted", 已授权);
        call.resolve(结果);
    }

    @PluginMethod
    public void openUsageAccessSettings(PluginCall call) {
        try {
            Intent intent = new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            Log.i(日志标签, "已打开使用情况访问设置页");
            call.resolve();
        } catch (Exception exception) {
            Log.e(日志标签, "打开使用情况访问设置页失败", exception);
            call.reject("打开使用情况访问设置页失败", exception);
        }
    }

    @PluginMethod
    public void queryScreenUsageEvents(PluginCall call) {
        long 开始时间 = call.getLong("startTime", 0L);
        long 结束时间 = call.getLong("endTime", System.currentTimeMillis());

        if (开始时间 <= 0 || 结束时间 <= 0 || 开始时间 > 结束时间) {
            call.reject("读取屏幕使用事件的时间区间无效");
            return;
        }

        if (!是否已授权使用情况访问()) {
            call.reject("尚未授权使用情况访问权限");
            return;
        }

        UsageStatsManager usageStatsManager = (UsageStatsManager) getContext().getSystemService(Context.USAGE_STATS_SERVICE);
        if (usageStatsManager == null) {
            call.reject("当前设备不支持使用情况统计服务");
            return;
        }

        Log.i(日志标签, "开始读取屏幕使用事件: " + 开始时间 + " - " + 结束时间);
        JSArray 事件列表 = new JSArray();
        UsageEvents usageEvents = usageStatsManager.queryEvents(开始时间, 结束时间);
        UsageEvents.Event event = new UsageEvents.Event();

        while (usageEvents.hasNextEvent()) {
            usageEvents.getNextEvent(event);
            String 映射类型 = 映射事件类型(event.getEventType());
            if (映射类型 == null) {
                continue;
            }

            JSObject 事件 = new JSObject();
            事件.put("type", 映射类型);
            事件.put("timestamp", event.getTimeStamp());
            事件列表.put(事件);
        }

        JSObject 结果 = new JSObject();
        结果.put("events", 事件列表);

        Log.i(日志标签, "屏幕使用事件读取完成，数量: " + 事件列表.length());
        call.resolve(结果);
    }

    private boolean 是否已授权使用情况访问() {
        AppOpsManager appOpsManager = (AppOpsManager) getContext().getSystemService(Context.APP_OPS_SERVICE);
        if (appOpsManager == null) {
            return false;
        }

        int mode = appOpsManager.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            Process.myUid(),
            getContext().getPackageName()
        );
        return mode == AppOpsManager.MODE_ALLOWED;
    }

    private String 映射事件类型(int eventType) {
        switch (eventType) {
            case UsageEvents.Event.SCREEN_INTERACTIVE:
                return "screen_interactive";
            case UsageEvents.Event.SCREEN_NON_INTERACTIVE:
                return "screen_non_interactive";
            case UsageEvents.Event.KEYGUARD_HIDDEN:
                return "keyguard_hidden";
            case UsageEvents.Event.KEYGUARD_SHOWN:
                return "keyguard_shown";
            default:
                return null;
        }
    }
}
