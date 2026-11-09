package br.com.walkietalkie

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

/** Keeps the active local-network session in a user-visible foreground process while the app is hidden. */
class VoriqPresenceService : Service() {
    override fun onCreate() {
        super.onCreate()
        criarCanal()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val abrirApp = Intent(this, MainActivity::class.java).apply {
            this.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val abrirPendente = PendingIntent.getActivity(
            this,
            PEDIDO_ABRIR,
            abrirApp,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notificacao = Notification.Builder(this, CANAL_PRESENCA)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("VORIQ conectado")
            .setContentText("Pronto para receber chamadas nesta rede Wi-Fi")
            .setCategory(Notification.CATEGORY_SERVICE)
            .setContentIntent(abrirPendente)
            .setOngoing(true)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                ID_NOTIFICACAO,
                notificacao,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE,
            )
        } else {
            startForeground(ID_NOTIFICACAO, notificacao)
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun criarCanal() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val canal = NotificationChannel(
                CANAL_PRESENCA,
                "Conexão VORIQ",
                NotificationManager.IMPORTANCE_LOW,
            ).apply {
                description = "Mostra quando o VORIQ está conectado e pronto para receber chamadas."
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(canal)
        }
    }

    companion object {
        private const val CANAL_PRESENCA = "voriq_presenca"
        private const val ID_NOTIFICACAO = 7101
        private const val PEDIDO_ABRIR = 7102
    }
}
