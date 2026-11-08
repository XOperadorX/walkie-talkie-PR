package br.com.walkietalkie

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.os.Bundle
import android.view.MotionEvent
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : android.app.Activity() {
    companion object {
        private const val PORTA = 5000
        private const val TAXA = 16000
        private const val MAX_AUDIO = 8192
        private const val PEDIDO_MICROFONE = 44
    }

    private lateinit var etIp: EditText
    private lateinit var etId: EditText
    private lateinit var etSenha: EditText
    private lateinit var btnConectar: Button
    private lateinit var btnFalar: Button
    private lateinit var tvStatus: TextView
    private val executor: ExecutorService = Executors.newCachedThreadPool()
    private val conectado = AtomicBoolean(false)
    private val falando = AtomicBoolean(false)
    @Volatile private var socket: Socket? = null
    @Volatile private var gravador: AudioRecord? = null
    @Volatile private var reprodutor: AudioTrack? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        etIp = findViewById(R.id.etIp)
        etId = findViewById(R.id.etId)
        etSenha = findViewById(R.id.etSenha)
        btnConectar = findViewById(R.id.btnConectar)
        btnFalar = findViewById(R.id.btnFalar)
        tvStatus = findViewById(R.id.tvStatus)
        btnConectar.setOnClickListener { conectar() }
        btnFalar.setOnTouchListener { _, evento ->
            if (!conectado.get()) return@setOnTouchListener false
            when (evento.action) {
                MotionEvent.ACTION_DOWN -> { iniciarGravacao(); true }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { pararGravacao(); true }
                else -> true
            }
        }
    }

    private fun conectar() {
        val ip = etIp.text.toString().trim()
        val id = etId.text.toString().trim()
        val senha = etSenha.text.toString()
        if (ip.isBlank() || id.isBlank() || senha.isBlank()) {
            aviso("Preencha o IP, o ID e a senha.")
            return
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), PEDIDO_MICROFONE)
            return
        }
        btnConectar.isEnabled = false
        status("Conectando...")
        executor.execute {
            try {
                val novo = Socket()
                novo.tcpNoDelay = true
                novo.connect(InetSocketAddress(ip, PORTA), 6000)
                socket = novo
                val saida = novo.getOutputStream()
                saida.write((JSONObject().put("tipo", "entrar").put("id", id).put("senha", senha).toString() + "\n").toByteArray(Charsets.UTF_8))
                saida.flush()
                val resposta = lerLinha(novo.getInputStream())
                val dados = JSONObject(resposta)
                if (dados.optString("status") != "ok") error(dados.optString("mensagem", "Falha no acesso."))
                conectado.set(true)
                iniciarReproducao(novo)
                runOnUiThread {
                    status("Conectado à sala geral")
                    btnFalar.isEnabled = true
                    btnConectar.text = "Desconectar"
                    btnConectar.isEnabled = true
                    btnConectar.setOnClickListener { desconectar() }
                }
            } catch (e: Exception) {
                desconectarSocket()
                runOnUiThread {
                    status("Desconectado")
                    btnConectar.isEnabled = true
                    aviso(e.message ?: "Não foi possível conectar.")
                }
            }
        }
    }

    private fun iniciarGravacao() {
        if (!falando.compareAndSet(false, true)) return
        executor.execute {
            var recorder: AudioRecord? = null
            try {
                val formato = AudioFormat.CHANNEL_IN_MONO
                val encoding = AudioFormat.ENCODING_PCM_16BIT
                val minimo = AudioRecord.getMinBufferSize(TAXA, formato, encoding)
                if (minimo <= 0) error("Este aparelho não disponibilizou o microfone.")
                recorder = AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION, TAXA, formato, encoding, maxOf(minimo, 4096))
                if (recorder.state != AudioRecord.STATE_INITIALIZED) error("Não foi possível iniciar o microfone.")
                gravador = recorder
                recorder.startRecording()
                status("Transmitindo... solte para encerrar")
                val buffer = ByteArray(4096)
                val output = socket?.getOutputStream() ?: error("Sem conexão com o servidor.")
                while (falando.get() && conectado.get()) {
                    val n = recorder.read(buffer, 0, buffer.size)
                    if (n > 0) {
                        synchronized(output) {
                            output.write(byteArrayOf((n shr 24).toByte(), (n shr 16).toByte(), (n shr 8).toByte(), n.toByte()))
                            output.write(buffer, 0, n)
                            output.flush()
                        }
                    }
                }
            } catch (e: Exception) {
                if (conectado.get()) runOnUiThread { aviso(e.message ?: "Erro no microfone.") }
            } finally {
                falando.set(false)
                try { recorder?.stop() } catch (_: Exception) { }
                recorder?.release()
                if (gravador === recorder) gravador = null
                if (conectado.get()) status("Conectado à sala geral")
            }
        }
    }

    private fun pararGravacao() {
        falando.set(false)
        try { gravador?.stop() } catch (_: Exception) { }
    }

    private fun iniciarReproducao(conexao: Socket) {
        val track = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(TAXA).setEncoding(AudioFormat.ENCODING_PCM_16BIT).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setBufferSizeInBytes(maxOf(AudioTrack.getMinBufferSize(TAXA, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT), 8192))
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
        reprodutor = track
        track.play()
        executor.execute {
            try {
                val input = conexao.getInputStream()
                val cabecalho = ByteArray(4)
                while (conectado.get() && !conexao.isClosed) {
                    lerExatamente(input, cabecalho)
                    val tamanho = ((cabecalho[0].toInt() and 255) shl 24) or ((cabecalho[1].toInt() and 255) shl 16) or ((cabecalho[2].toInt() and 255) shl 8) or (cabecalho[3].toInt() and 255)
                    if (tamanho !in 1..MAX_AUDIO) error("Bloco de áudio inválido.")
                    val audio = ByteArray(tamanho)
                    lerExatamente(input, audio)
                    var offset = 0
                    while (offset < audio.size) {
                        val escritos = track.write(audio, offset, audio.size - offset)
                        if (escritos < 0) error("Falha ao reproduzir áudio.")
                        offset += escritos
                    }
                }
            } catch (_: Exception) {
                if (conectado.get()) runOnUiThread { desconectar(); status("Conexão encerrada") }
            }
        }
    }

    private fun lerExatamente(input: java.io.InputStream, buffer: ByteArray) {
        var offset = 0
        while (offset < buffer.size) {
            val lidos = input.read(buffer, offset, buffer.size - offset)
            if (lidos < 0) throw java.io.EOFException("Servidor desconectado.")
            offset += lidos
        }
    }

    private fun lerLinha(input: java.io.InputStream): String {
        val bytes = java.io.ByteArrayOutputStream()
        while (bytes.size() <= 4096) {
            val valor = input.read()
            if (valor < 0) throw java.io.EOFException("O servidor encerrou a conexão.")
            if (valor == '\n'.code) return bytes.toString(Charsets.UTF_8.name())
            bytes.write(valor)
        }
        error("Resposta do servidor muito longa.")
    }

    private fun desconectar() {
        conectado.set(false)
        falando.set(false)
        pararGravacao()
        desconectarSocket()
        runOnUiThread {
            btnFalar.isEnabled = false
            btnConectar.text = "Conectar"
            btnConectar.isEnabled = true
            btnConectar.setOnClickListener { conectar() }
            status("Desconectado")
        }
    }

    private fun desconectarSocket() {
        try { socket?.close() } catch (_: Exception) { }
        socket = null
        try { reprodutor?.pause(); reprodutor?.flush(); reprodutor?.release() } catch (_: Exception) { }
        reprodutor = null
    }

    private fun status(texto: String) = runOnUiThread { tvStatus.text = texto }
    private fun aviso(texto: String) = runOnUiThread { Toast.makeText(this, texto, Toast.LENGTH_LONG).show() }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PEDIDO_MICROFONE) {
            if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) conectar()
            else aviso("O app precisa da permissão do microfone para transmitir voz.")
        }
    }

    override fun onDestroy() {
        conectado.set(false)
        falando.set(false)
        pararGravacao()
        desconectarSocket()
        executor.shutdownNow()
        super.onDestroy()
    }
}
