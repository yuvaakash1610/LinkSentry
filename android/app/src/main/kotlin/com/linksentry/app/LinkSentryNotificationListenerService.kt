package com.linksentry.app

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

/**
 * LinkSentry Native Android NotificationListenerService Integration
 * 
 * Inspects incoming notification previews from user-selected apps (e.g. SMS, WhatsApp)
 * to detect malicious link patterns and alert the user.
 * 
 * Safeguards:
 * - Requires explicit user permission in Android Notification Access settings.
 * - Does NOT store raw text remotely.
 * - Operates entirely under user control.
 */
class LinkSentryNotificationListenerService : NotificationListenerService() {

    companion object {
        private const val TAG = "LinkSentryNotifService"
        var isLiveProtectionActive: Boolean = false
        var monitoredApps: HashSet<String> = hashSetOf("com.google.android.apps.messaging", "com.whatsapp", "org.telegram.messenger")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)

        if (!isLiveProtectionActive || sbn == null) return

        val packageName = sbn.packageName
        val extras = sbn.notification.extras
        val title = extras.getString("android.title") ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        Log.d(TAG, "Notification received from package: $packageName | Title: $title")

        // Check if text contains URL or suspicious patterns
        if (text.contains("http://") || text.contains("https://") || text.contains("KYC", ignoreCase = true)) {
            Log.w(TAG, "Suspicious link or alert pattern detected in notification!")
            // Transmit event to Flutter platform channel
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
    }
}
