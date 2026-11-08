package br.com.walkietalkie

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.media.ToneGenerator
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.net.wifi.WifiInfo
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import android.view.MotionEvent
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.io.EOFException
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.net.SocketTimeoutException
import java.nio.ByteBuffer
import java.security.KeyStore
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class MainActivity : android.app.Activity() {
    companion object {
        private const val PORTA_DESCOBERTA = 5001
        private const val TAXA = 16000
        private const val MAX_AUDIO = 8192
        private const val MAX_CONTROLE = 16384
        private const val PEDIDO_MICROFONE = 44
        private const val PEDIDO_LOCALIZACAO_WIFI = 45
        private const val TOKEN_DESCOBERTA = "NEXTEL_LOCAL_DISCOVER_V1"
        private const val PREFERENCIAS = "acesso_protegido"
        private const val ALIAS_CHAVE = "nextel_local_credenciais_v1"
    }

    private lateinit var etId: EditText
    private lateinit var etSenha: EditText
    private lateinit var telaLogin: LinearLayout
    private lateinit var telaPrincipal: LinearLayout
    private lateinit var btnConectar: Button
    private lateinit var btnDesconectar: Button
    private lateinit var btnFalar: Button
    private lateinit var btnAceitar: Button
    private lateinit var btnRecusar: Button
    private lateinit var btnEncerrar: Button
    private lateinit var tvStatusLogin: TextView
    private lateinit var tvStatusPrincipal: TextView
    private lateinit var tvWifiLogin: TextView
    private lateinit var tvWifiPrincipal: TextView
    private lateinit var tvChamada: TextView
    private lateinit var layoutFavoritos: LinearLayout
    private lateinit var layoutUsuarios: LinearLayout

    private val executor: ExecutorService = Executors.newCachedThreadPool()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val conectado = AtomicBoolean(false)
    private val falando = AtomicBoolean(false)
    private val chamadaPendente = AtomicBoolean(false)
    private val chamadaAtiva = AtomicBoolean(false)
    private val travaSaida = Any()

    @Volatile private var socket: Socket? = null
    @Volatile private var redeWifi: Network? = null
    @Volatile private var gravador: AudioRecord? = null
    @Volatile private var reprodutor: AudioTrack? = null
    @Volatile private var chamadaId: String? = null
    @Volatile private var nomeContato: String? = null
    @Volatile private var destinoNome: String? = null
    @Volatile private var recebendoConvite = false
    private var solicitouPermissaoNomeWifi = false

    private data class UsuarioOnline(val id: String, val nome: String)
    private var usuariosOnline: List<UsuarioOnline> = emptyList()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        telaLogin = findViewById(R.id.telaLogin)
        telaPrincipal = findViewById(R.id.telaPrincipal)
        etId = findViewById(R.id.etId)
        etSenha = findViewById(R.id.etSenha)
        btnConectar = findViewById(R.id.btnConectar)
        btnDesconectar = findViewById(R.id.btnDesconectar)
        btnFalar = findViewById(R.id.btnFalar)
        btnAceitar = findViewById(R.id.btnAceitar)
        btnRecusar = findViewById(R.id.btnRecusar)
        btnEncerrar = findViewById(R.id.btnEncerrar)
        tvStatusLogin = findViewById(R.id.tvStatusLogin)
        tvStatusPrincipal = findViewById(R.id.tvStatusPrincipal)
        tvWifiLogin = findViewById(R.id.tvWifiLogin)
        tvWifiPrincipal = findViewById(R.id.tvWifiPrincipal)
        tvChamada = findViewById(R.id.tvChamada)
        layoutFavoritos = findViewById(R.id.layoutFavoritos)
        layoutUsuarios = findViewById(R.id.layoutUsuarios)

        carregarCredenciais()
        atualizarNomeWifiInterface()
        btnConectar.setOnClickListener { conectar() }
        btnDesconectar.setOnClickListener { desconectar("Desconectado") }
        btnAceitar.setOnClickListener { aceitarChamada() }
        btnRecusar.setOnClickListener { recusarChamada() }
        btnEncerrar.setOnClickListener { encerrarChamadaLocal() }
        btnFalar.setOnTouchListener { _, evento ->
            if (!chamadaAtiva.get()) return@setOnTouchListener false
            when (evento.action) {
                MotionEvent.ACTION_DOWN -> { iniciarGravacao(); true }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { pararGravacao(); true }
                else -> true
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (::tvWifiLogin.isInitialized) atualizarNomeWifiInterface()
    }

    private fun conectar() {
        val id = etId.text.toString().trim()
        val senha = etSenha.text.toString()
        if (id.isBlank() || senha.isBlank()) {
            aviso("Digite seu ID e sua senha.")
            return
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), PEDIDO_MICROFONE)
            return
        }
        if (!solicitouPermissaoNomeWifi && checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            solicitouPermissaoNomeWifi = true
            status("Para mostrar o nome do Wi-Fi, permita a localização. O app usa essa permissão apenas para ler o nome da rede.")
            requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), PEDIDO_LOCALIZACAO_WIFI)
            return
        }

        btnConectar.isEnabled = false
        status("Conectando à rede Wi-Fi...")
        executor.execute {
            var novaConexao: Socket? = null
            try {
                val wifi = procurarRedeWifi()
                // Use the same current-connection lookup shown on screen 1.
                // The Network-specific WifiInfo can be redacted by Android.
                val nomeWifi = obterNomeWifi()
                val servidor = descobrirServidor(wifi)
                novaConexao = Socket()
                wifi.bindSocket(novaConexao)
                novaConexao.tcpNoDelay = true
                novaConexao.connect(InetSocketAddress(servidor.first, servidor.second), 6000)
                val saida = novaConexao.getOutputStream()
                saida.write((JSONObject().put("tipo", "entrar").put("id", id).put("senha", senha).toString() + "\n").toByteArray(Charsets.UTF_8))
                saida.flush()
                val dados = JSONObject(lerLinha(novaConexao.getInputStream()))
                if (dados.optString("status") != "ok") {
                    error(dados.optString("mensagem", "ID ou senha incorretos."))
                }

                socket = novaConexao
                redeWifi = wifi
                conectado.set(true)
                try {
                    salvarCredenciais(id, senha)
                } catch (_: Exception) {
                    runOnUiThread { aviso("Conectado. O aparelho não conseguiu proteger o salvamento do ID e da senha.") }
                }
                val conexaoFinal = novaConexao
                runOnUiThread {
                    btnConectar.isEnabled = true
                    tvWifiLogin.text = nomeWifi
                    tvWifiPrincipal.text = nomeWifi
                    mostrarTelaPrincipal()
                    status("Conectado. Escolha uma pessoa para chamar.")
                    renderizarUsuarios()
                }
                executor.execute { receberPacotes(conexaoFinal) }
            } catch (e: Exception) {
                try { novaConexao?.close() } catch (_: Exception) { }
                runOnUiThread {
                    btnConectar.isEnabled = true
                    status("Desconectado")
                    aviso(e.message ?: "Não foi possível conectar.")
                }
            }
        }
    }

    private fun procurarRedeWifi(): Network {
        val gerente = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val redes = (listOfNotNull(gerente.activeNetwork) + gerente.allNetworks.toList()).distinct()
        return redes.firstOrNull { rede ->
            gerente.getNetworkCapabilities(rede)?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true
        } ?: error("Conecte o celular ao Wi-Fi onde está o servidor e tente novamente.")
    }

    @Suppress("DEPRECATION")
    private fun obterNomeWifi(rede: Network? = null): String {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return "Wi-Fi conectado: permita o acesso à localização para mostrar o nome da rede."
        }
        return try {
            val gerente = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val infoDaRede = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && rede != null) {
                gerente.getNetworkCapabilities(rede)?.transportInfo as? WifiInfo
            } else null
            val wifiInfo = infoDaRede
                ?: (applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager).connectionInfo
            val nome = wifiInfo?.ssid?.trim('"')
            if (nome.isNullOrBlank() || nome == WifiManager.UNKNOWN_SSID || nome == "<unknown ssid>") {
                "Wi-Fi conectado: nome indisponível"
            } else {
                "Wi-Fi conectado: $nome"
            }
        } catch (_: Exception) {
            "Wi-Fi conectado: nome indisponível"
        }
    }

    private fun atualizarNomeWifiInterface(rede: Network? = null) {
        val nome = obterNomeWifi(rede)
        tvWifiLogin.text = nome
        if (conectado.get()) tvWifiPrincipal.text = nome
    }

    private fun mostrarTelaPrincipal() {
        telaLogin.visibility = android.view.View.GONE
        telaPrincipal.visibility = android.view.View.VISIBLE
    }

    private fun mostrarTelaLogin() {
        telaPrincipal.visibility = android.view.View.GONE
        telaLogin.visibility = android.view.View.VISIBLE
    }

    private fun enderecosBroadcast(): List<InetAddress> {
        val enderecos = linkedSetOf<InetAddress>()
        try {
            val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val dhcp = wifi.dhcpInfo
            if (dhcp.ipAddress != 0 && dhcp.netmask != 0) {
                val broadcast = (dhcp.ipAddress and dhcp.netmask) or dhcp.netmask.inv()
                val bytes = ByteArray(4) { indice -> ((broadcast shr (indice * 8)) and 0xff).toByte() }
                enderecos.add(InetAddress.getByAddress(bytes))
            }
        } catch (_: Exception) { }
        enderecos.add(InetAddress.getByName("255.255.255.255"))
        return enderecos.toList()
    }

    private fun descobrirServidor(wifi: Network): Pair<InetAddress, Int> {
        val descoberta = DatagramSocket(null)
        try {
            wifi.bindSocket(descoberta)
            descoberta.broadcast = true
            descoberta.soTimeout = 700
            descoberta.bind(InetSocketAddress(0))
            val pedido = TOKEN_DESCOBERTA.toByteArray(Charsets.UTF_8)
            val enderecos = enderecosBroadcast()
            repeat(4) {
                for (endereco in enderecos) {
                    try {
                        descoberta.send(DatagramPacket(pedido, pedido.size, endereco, PORTA_DESCOBERTA))
                    } catch (_: Exception) { }
                }
                val buffer = ByteArray(1024)
                val resposta = DatagramPacket(buffer, buffer.size)
                try {
                    descoberta.receive(resposta)
                    val dados = JSONObject(String(resposta.data, 0, resposta.length, Charsets.UTF_8))
                    if (dados.optString("service") == "nextel-local") {
                        return Pair(resposta.address, dados.optInt("port", 5000))
                    }
                } catch (_: SocketTimeoutException) { }
            }
        } finally {
            descoberta.close()
        }
        error("Não encontrei o servidor. Confirme que o computador e o celular estão no mesmo Wi-Fi e que o servidor está aberto.")
    }

    private fun receberPacotes(conexao: Socket) {
        try {
            val input = conexao.getInputStream()
            while (conectado.get() && !conexao.isClosed) {
                val tipo = input.read()
                if (tipo < 0) throw EOFException("Servidor desconectado.")
                val cabecalho = ByteArray(4)
                lerExatamente(input, cabecalho)
                val tamanho = ByteBuffer.wrap(cabecalho).int
                when (tipo.toChar()) {
                    'C' -> {
                        if (tamanho !in 1..MAX_CONTROLE) error("Mensagem de controle inválida.")
                        val mensagem = ByteArray(tamanho)
                        lerExatamente(input, mensagem)
                        processarControle(JSONObject(String(mensagem, Charsets.UTF_8)))
                    }
                    'A' -> {
                        if (tamanho !in 1..MAX_AUDIO) error("Bloco de áudio inválido.")
                        val audio = ByteArray(tamanho)
                        lerExatamente(input, audio)
                        reproduzirAudio(audio)
                    }
                    else -> error("Tipo de pacote desconhecido.")
                }
            }
        } catch (e: Exception) {
            if (conectado.get()) runOnUiThread { desconectar("A conexão com o servidor foi encerrada.") }
        }
    }

    private fun processarControle(mensagem: JSONObject) {
        when (mensagem.optString("tipo")) {
            "usuarios_online" -> {
                val lista = mutableListOf<UsuarioOnline>()
                val jsonLista = mensagem.optJSONArray("usuarios") ?: JSONArray()
                for (i in 0 until jsonLista.length()) {
                    val usuario = jsonLista.optJSONObject(i) ?: continue
                    val id = usuario.optString("id")
                    val nome = usuario.optString("nome")
                    if (id.isNotBlank()) lista.add(UsuarioOnline(id, nome))
                }
                usuariosOnline = lista
                runOnUiThread { renderizarUsuarios() }
            }
            "convite" -> {
                chamadaId = mensagem.optString("chamada_id")
                nomeContato = mensagem.optString("origem_nome", "Usuário")
                recebendoConvite = true
                chamadaPendente.set(true)
                tocarBip()
                runOnUiThread {
                    tvChamada.text = "${nomeContato ?: "Alguém"} está chamando. Aceita?"
                    btnAceitar.visibility = android.view.View.VISIBLE
                    btnRecusar.visibility = android.view.View.VISIBLE
                    btnEncerrar.visibility = android.view.View.GONE
                    btnFalar.isEnabled = false
                    btnFalar.text = "Aceite a chamada para falar"
                    renderizarUsuarios()
                }
            }
            "chamada_enviada" -> {
                chamadaId = mensagem.optString("chamada_id")
                destinoNome = mensagem.optString("destino_nome", "usuário")
                recebendoConvite = false
                chamadaPendente.set(true)
                runOnUiThread {
                    tvChamada.text = "Chamando ${destinoNome ?: "usuário"}... Aguarde a resposta."
                    btnFalar.isEnabled = false
                    btnFalar.text = "Aguarde o aceite para falar"
                    btnAceitar.visibility = android.view.View.GONE
                    btnRecusar.visibility = android.view.View.GONE
                    btnEncerrar.visibility = android.view.View.VISIBLE
                    renderizarUsuarios()
                }
            }
            "chamada_aceita" -> {
                chamadaId = mensagem.optString("chamada_id")
                nomeContato = mensagem.optString("nome", destinoNome ?: "contato")
                chamadaPendente.set(false)
                recebendoConvite = false
                chamadaAtiva.set(true)
                try {
                    iniciarReproducao()
                } catch (e: Exception) {
                    aviso(e.message ?: "Não foi possível iniciar o áudio.")
                    encerrarChamadaLocal()
                    return
                }
                runOnUiThread {
                    tvChamada.text = "Em chamada com ${nomeContato ?: "contato"}. Segure o botão para falar."
                    btnAceitar.visibility = android.view.View.GONE
                    btnRecusar.visibility = android.view.View.GONE
                    btnEncerrar.visibility = android.view.View.VISIBLE
                    btnFalar.isEnabled = true
                    btnFalar.text = "Toque e segure para falar"
                    renderizarUsuarios()
                }
            }
            "chamada_encerrada" -> {
                val motivo = mensagem.optString("motivo")
                limparChamada()
                runOnUiThread {
                    tvChamada.text = when (motivo) {
                        "sem_resposta" -> "A chamada não foi atendida."
                        "recusada" -> "A chamada foi recusada."
                        "conexao_perdida" -> "A conexão com a outra pessoa foi perdida."
                        else -> "Chamada encerrada."
                    }
                    renderizarUsuarios()
                }
            }
            "erro" -> {
                chamadaPendente.set(false)
                chamadaId = null
                recebendoConvite = false
                runOnUiThread {
                    tvChamada.text = mensagem.optString("mensagem", "Não foi possível iniciar a chamada.")
                    btnFalar.isEnabled = false
                    btnFalar.text = "Toque e segure para falar"
                    btnAceitar.visibility = android.view.View.GONE
                    btnRecusar.visibility = android.view.View.GONE
                    btnEncerrar.visibility = android.view.View.GONE
                    renderizarUsuarios()
                    aviso(mensagem.optString("mensagem", "Erro na chamada."))
                }
            }
        }
    }

    private fun renderizarUsuarios() {
        if (!::layoutUsuarios.isInitialized || !::layoutFavoritos.isInitialized) return
        layoutFavoritos.removeAllViews()
        layoutUsuarios.removeAllViews()
        val meuId = etId.text.toString().trim()
        if (!conectado.get()) {
            adicionarMensagemLista(layoutFavoritos, "Entre para ver seus favoritos.")
            adicionarMensagemLista(layoutUsuarios, "Entre para ver quem está disponível.")
            return
        }

        val favoritos = carregarFavoritos()
        for (id in favoritos.sorted()) {
            if (id == meuId) continue
            val usuario = usuariosOnline.firstOrNull { it.id == id }
            adicionarLinhaPessoa(
                layoutFavoritos,
                id,
                usuario?.nome ?: "ID favorito (offline)",
                favorito = true,
                online = usuario != null,
            )
        }
        if (layoutFavoritos.childCount == 0) adicionarMensagemLista(layoutFavoritos, "Toque na estrela de uma pessoa para adicioná-la.")

        val disponiveis = usuariosOnline.filter { it.id != meuId && it.id !in favoritos }
        for (usuario in disponiveis) {
            adicionarLinhaPessoa(layoutUsuarios, usuario.id, usuario.nome, favorito = false, online = true)
        }
        if (disponiveis.isEmpty()) adicionarMensagemLista(layoutUsuarios, "Nenhuma outra pessoa online fora dos favoritos.")
    }

    private fun adicionarMensagemLista(lista: LinearLayout, texto: String) {
        val mensagem = TextView(this).apply {
            this.text = texto
            setTextColor(0xff52687b.toInt())
            setPadding(8, 12, 8, 12)
        }
        lista.addView(mensagem)
    }

    private fun adicionarLinhaPessoa(lista: LinearLayout, id: String, nome: String, favorito: Boolean, online: Boolean) {
        val linha = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            setPadding(4, 3, 4, 3)
        }
        val identidade = TextView(this).apply {
            text = "$nome\n$id"
            setTextColor(0xff18324a.toInt())
            textSize = 14f
            setPadding(8, 8, 4, 8)
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        val chamar = Button(this).apply {
            text = if (online) "Chamar" else "Offline"
            isAllCaps = false
            isEnabled = online && !chamadaPendente.get() && !chamadaAtiva.get()
            setOnClickListener { iniciarChamada(id, nome) }
        }
        val estrela = Button(this).apply {
            text = if (favorito) "★" else "☆"
            contentDescription = if (favorito) "Remover $id dos favoritos" else "Adicionar $id aos favoritos"
            isAllCaps = false
            setOnClickListener { alternarFavorito(id) }
        }
        linha.addView(identidade)
        linha.addView(chamar)
        linha.addView(estrela)
        lista.addView(linha)
    }

    private fun carregarFavoritos(): Set<String> = getSharedPreferences("preferencias_local", MODE_PRIVATE)
        .getStringSet("favoritos", mutableSetOf())?.toSet() ?: emptySet()

    private fun alternarFavorito(id: String) {
        val favoritos = carregarFavoritos().toMutableSet()
        if (!favoritos.add(id)) favoritos.remove(id)
        getSharedPreferences("preferencias_local", MODE_PRIVATE).edit()
            .putStringSet("favoritos", favoritos)
            .apply()
        renderizarUsuarios()
    }

    private fun iniciarChamada(id: String, nome: String) {
        if (!conectado.get() || chamadaPendente.get() || chamadaAtiva.get()) return
        chamadaPendente.set(true)
        destinoNome = nome
        tvChamada.text = "Chamando $nome..."
        renderizarUsuarios()
        enviarControle(JSONObject().put("tipo", "chamar").put("destino", id))
    }

    private fun aceitarChamada() {
        val id = chamadaId ?: return
        enviarControle(JSONObject().put("tipo", "aceitar").put("chamada_id", id))
        btnAceitar.isEnabled = false
        tvChamada.text = "Aceitando chamada..."
    }

    private fun recusarChamada() {
        val id = chamadaId ?: return
        enviarControle(JSONObject().put("tipo", "recusar").put("chamada_id", id))
        limparChamada()
        tvChamada.text = "Chamada recusada."
        renderizarUsuarios()
    }

    private fun encerrarChamadaLocal() {
        val id = chamadaId
        if (id != null) enviarControle(JSONObject().put("tipo", if (recebendoConvite) "recusar" else "encerrar").put("chamada_id", id))
        limparChamada()
        tvChamada.text = "Chamada encerrada."
        renderizarUsuarios()
    }

    private fun limparChamada() {
        chamadaPendente.set(false)
        chamadaAtiva.set(false)
        falando.set(false)
        chamadaId = null
        nomeContato = null
        destinoNome = null
        recebendoConvite = false
        pararGravacao()
        pararReproducao()
        runOnUiThread {
            btnFalar.isEnabled = false
            btnFalar.text = "Toque e segure para falar"
            btnAceitar.visibility = android.view.View.GONE
            btnAceitar.isEnabled = true
            btnRecusar.visibility = android.view.View.GONE
            btnEncerrar.visibility = android.view.View.GONE
        }
    }

    private fun iniciarGravacao() {
        if (!chamadaAtiva.get() || !falando.compareAndSet(false, true)) return
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
                status("Falando com ${nomeContato ?: "contato"}... solte para encerrar")
                val buffer = ByteArray(4096)
                while (falando.get() && conectado.get() && chamadaAtiva.get()) {
                    val lidos = recorder.read(buffer, 0, buffer.size)
                    if (lidos > 0) enviarPacote('A', buffer.copyOf(lidos))
                }
            } catch (e: Exception) {
                if (conectado.get() && chamadaAtiva.get()) runOnUiThread { aviso(e.message ?: "Erro no microfone.") }
            } finally {
                falando.set(false)
                try { recorder?.stop() } catch (_: Exception) { }
                recorder?.release()
                if (gravador === recorder) gravador = null
                if (conectado.get() && chamadaAtiva.get()) status("Em chamada com ${nomeContato ?: "contato"}. Segure para falar.")
            }
        }
    }

    private fun pararGravacao() {
        falando.set(false)
        try { gravador?.stop() } catch (_: Exception) { }
    }

    private fun iniciarReproducao() {
        if (reprodutor != null) return
        val minimo = AudioTrack.getMinBufferSize(TAXA, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
        if (minimo <= 0) error("O aparelho não disponibilizou a reprodução de áudio.")
        reprodutor = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(TAXA).setEncoding(AudioFormat.ENCODING_PCM_16BIT).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setBufferSizeInBytes(maxOf(minimo, 8192))
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build().also { it.play() }
    }

    private fun reproduzirAudio(audio: ByteArray) {
        if (!chamadaAtiva.get()) return
        val track = reprodutor ?: return
        var offset = 0
        while (offset < audio.size && chamadaAtiva.get()) {
            val escritos = track.write(audio, offset, audio.size - offset)
            if (escritos < 0) error("Falha ao reproduzir o áudio.")
            offset += escritos
        }
    }

    private fun pararReproducao() {
        try { reprodutor?.pause(); reprodutor?.flush(); reprodutor?.release() } catch (_: Exception) { }
        reprodutor = null
    }

    private fun tocarBip() {
        val toque = try { ToneGenerator(AudioManager.STREAM_NOTIFICATION, 85) } catch (_: Exception) { return }
        toque.startTone(ToneGenerator.TONE_PROP_BEEP, 170)
        mainHandler.postDelayed({ toque.startTone(ToneGenerator.TONE_PROP_BEEP, 170) }, 260)
        mainHandler.postDelayed({ toque.release() }, 520)
    }

    private fun enviarControle(mensagem: JSONObject) {
        try {
            enviarPacote('C', mensagem.toString().toByteArray(Charsets.UTF_8))
        } catch (e: Exception) {
            if (conectado.get()) {
                aviso("A conexão com o servidor foi interrompida. Entre novamente para fazer a chamada.")
                desconectar("Conexão com o servidor interrompida.", avisarServidor = false)
            }
        }
    }

    private fun enviarPacote(tipo: Char, dados: ByteArray) {
        val limite = if (tipo == 'A') MAX_AUDIO else MAX_CONTROLE
        require(dados.isNotEmpty() && dados.size <= limite) { "Pacote muito grande." }
        val saida = socket?.getOutputStream() ?: error("Sem conexão com o servidor.")
        synchronized(travaSaida) {
            saida.write(tipo.code)
            saida.write(ByteBuffer.allocate(4).putInt(dados.size).array())
            saida.write(dados)
            saida.flush()
        }
    }

    private fun salvarCredenciais(id: String, senha: String) {
        getSharedPreferences(PREFERENCIAS, MODE_PRIVATE).edit()
            .putString("id", cifrar(id))
            .putString("senha", cifrar(senha))
            .apply()
    }

    private fun carregarCredenciais() {
        val preferencias = getSharedPreferences(PREFERENCIAS, MODE_PRIVATE)
        try {
            etId.setText(preferencias.getString("id", null)?.let { decifrar(it) } ?: "")
            etSenha.setText(preferencias.getString("senha", null)?.let { decifrar(it) } ?: "")
        } catch (_: Exception) {
            preferencias.edit().clear().apply()
        }
    }

    private fun chaveCredenciais(): SecretKey {
        val armazenamento = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (armazenamento.getKey(ALIAS_CHAVE, null) as? SecretKey)?.let { return it }
        val gerador = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        gerador.init(KeyGenParameterSpec.Builder(ALIAS_CHAVE, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true)
            .build())
        return gerador.generateKey()
    }

    private fun cifrar(texto: String): String {
        val cifra = Cipher.getInstance("AES/GCM/NoPadding")
        cifra.init(Cipher.ENCRYPT_MODE, chaveCredenciais())
        val iv = cifra.iv
        val criptografado = cifra.doFinal(texto.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(iv + criptografado, Base64.NO_WRAP)
    }

    private fun decifrar(valor: String): String {
        val combinado = Base64.decode(valor, Base64.NO_WRAP)
        require(combinado.size > 12) { "Credencial protegida inválida." }
        val iv = combinado.copyOfRange(0, 12)
        val conteudo = combinado.copyOfRange(12, combinado.size)
        val cifra = Cipher.getInstance("AES/GCM/NoPadding")
        cifra.init(Cipher.DECRYPT_MODE, chaveCredenciais(), GCMParameterSpec(128, iv))
        return String(cifra.doFinal(conteudo), Charsets.UTF_8)
    }

    private fun desconectar(mensagem: String = "Desconectado", avisarServidor: Boolean = true) {
        val estavaConectado = conectado.getAndSet(false)
        if (avisarServidor && estavaConectado) {
            chamadaId?.let { id ->
                try { enviarPacote('C', JSONObject().put("tipo", "encerrar").put("chamada_id", id).toString().toByteArray(Charsets.UTF_8)) } catch (_: Exception) { }
            }
        }
        chamadaPendente.set(false)
        chamadaAtiva.set(false)
        falando.set(false)
        pararGravacao()
        pararReproducao()
        try { socket?.close() } catch (_: Exception) { }
        socket = null
        redeWifi = null
        chamadaId = null
        recebendoConvite = false
        usuariosOnline = emptyList()
        runOnUiThread {
            btnConectar.isEnabled = true
            btnFalar.isEnabled = false
            btnAceitar.visibility = android.view.View.GONE
            btnRecusar.visibility = android.view.View.GONE
            btnEncerrar.visibility = android.view.View.GONE
            tvChamada.text = "Nenhuma chamada"
            mostrarTelaLogin()
            atualizarNomeWifiInterface()
            status(mensagem)
            renderizarUsuarios()
        }
    }

    private fun lerExatamente(input: java.io.InputStream, buffer: ByteArray) {
        var offset = 0
        while (offset < buffer.size) {
            val lidos = input.read(buffer, offset, buffer.size - offset)
            if (lidos < 0) throw EOFException("Servidor desconectado.")
            offset += lidos
        }
    }

    private fun lerLinha(input: java.io.InputStream): String {
        val bytes = java.io.ByteArrayOutputStream()
        while (bytes.size() <= 4096) {
            val valor = input.read()
            if (valor < 0) throw EOFException("O servidor encerrou a conexão.")
            if (valor == '\n'.code) return bytes.toString(Charsets.UTF_8.name())
            bytes.write(valor)
        }
        error("Resposta do servidor muito longa.")
    }

    private fun status(texto: String) = runOnUiThread {
        tvStatusLogin.text = texto
        tvStatusPrincipal.text = texto
    }
    private fun aviso(texto: String) = runOnUiThread { Toast.makeText(this, texto, Toast.LENGTH_LONG).show() }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PEDIDO_MICROFONE) {
            if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) conectar()
            else aviso("O app precisa da permissão do microfone para conversar.")
        } else if (requestCode == PEDIDO_LOCALIZACAO_WIFI) {
            atualizarNomeWifiInterface()
            conectar()
        }
    }

    @Deprecated("Deprecated in Android API")
    override fun onBackPressed() {
        if (conectado.get()) desconectar("Desconectado") else super.onBackPressed()
    }

    override fun onDestroy() {
        conectado.set(false)
        falando.set(false)
        pararGravacao()
        pararReproducao()
        try { socket?.close() } catch (_: Exception) { }
        executor.shutdownNow()
        super.onDestroy()
    }
}
