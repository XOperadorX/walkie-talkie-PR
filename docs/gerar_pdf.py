"""Generate the current beginner guide PDF using only Python's standard library."""
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
DESTINATIONS = [ROOT / "docs" / "guia_do_usuario.pdf", ROOT / "output" / "pdf" / "VORIQ_Guia_do_Usuario.pdf"]
WIDTH, HEIGHT = 595, 842
VERSION = "1.12"


def encoded(text):
    return text.encode("cp1252", errors="replace").hex().upper().encode("ascii")


def build_page(sections, page_number):
    commands = [b"q", b"0.024 0.071 0.145 rg", b"0 0 595 842 re f", b"Q"]
    y = 790

    def line(text, size=10, bold=False, color="0.91 0.95 1", indent=52, leading=None):
        nonlocal y
        leading = leading or round(size * 1.45)
        width = max(35, int((540 - indent) / (size * 0.51)))
        wrapped = textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False) or [""]
        for fragment in wrapped:
            commands.append(b"BT /%s %d Tf %s rg 1 0 0 1 %d %d Tm <%s> Tj ET" % (
                b"F2" if bold else b"F1", size, color.encode("ascii"), indent, y, encoded(fragment)))
            y -= leading

    for kind, value in sections:
        if kind == "title":
            commands += [b"0.03 0.10 0.20 rg", f"0 700 {WIDTH} 142 re f".encode()]
            line(value, 24, True, "1 1 1", 52, 34)
            y -= 8
        elif kind == "heading":
            y -= 6
            line(value, 14, True, "0.09 0.82 0.94", 52, 20)
            y -= 2
        elif kind == "step":
            line(value, 9.5, False, indent=65, leading=13)
            y -= 2
        elif kind == "note":
            line(value, 9, True, "0.35 0.88 0.96", 60, 13)
            y -= 3
        else:
            line(value, 9.5, False, indent=52, leading=14)
            y -= 3

    commands += [b"0.38 0.49 0.59 RG 0.5 w 52 42 m 543 42 l S"]
    footer = encoded(f"VORIQ | Guia do usuario | versao {VERSION}")
    commands += [b"BT /F1 8 Tf 0.38 0.49 0.59 rg 1 0 0 1 52 27 Tm <" + footer + b"> Tj ET"]
    commands += [f"BT /F1 8 Tf 0.38 0.49 0.59 rg 1 0 0 1 530 27 Tm <{page_number:02d}> Tj ET".encode()]
    return b"\n".join(commands)


pages = [
    [
        ("title", "VORIQ | Guia do celular"),
        ("heading", "O que este aplicativo faz"),
        ("body", "O app tem duas telas: a primeira pede ID e senha e mostra o nome do Wi-Fi; a segunda mostra o comunicador e atalhos. Toque em Contatos para abrir favoritos e pessoas disponíveis. Uma pessoa chama, a outra ouve dois bipes e aceita. Depois, cada pessoa segura o botão para falar e solta para parar."),
        ("heading", "Antes de começar"),
        ("step", "1. Tenha um computador Windows com Python 3.10 ou mais novo."),
        ("step", "2. Cada participante precisa de um celular Android 8.0 ou mais novo."),
        ("step", "3. Conecte todos ao mesmo Wi-Fi. O computador e o servidor precisam permanecer ligados."),
        ("heading", "1. Iniciar o servidor no computador"),
        ("step", "1. Abra a pasta do projeto no computador."),
        ("step", "2. Abra o PowerShell nessa pasta e execute: python servidor/servidor_walkie.py"),
        ("step", "3. Se o Firewall do Windows perguntar, permita Python em redes privadas."),
        ("step", "4. Deixe a janela do servidor aberta."),
        ("note", "O IP mostrado no terminal serve para abrir a página de cadastro. Você não precisa digitar IP no aplicativo."),
        ("body", "O servidor usa TCP 8080 para a página, TCP 5000 para as chamadas e UDP 5001 para o app localizar o servidor automaticamente."),
        ("body", "O menu do site tem Início, Criar acesso e APK. Use Criar acesso para fazer sua conta e APK para baixar o instalador."),
        ("heading", "2. Criar seu acesso"),
        ("step", "1. Em um navegador no mesmo Wi-Fi, abra o endereço impresso no terminal (exemplo: http://192.168.0.10:8080)."),
        ("step", "2. Informe seu nome e crie uma senha com pelo menos 8 caracteres. Toque em Cadastrar."),
        ("step", "3. Guarde o ID exibido e a senha. Cada pessoa cria seu proprio acesso."),
        ("note", "Cada pessoa use seu ID. Entrar com o mesmo ID em outro celular substitui a sessão anterior."),
    ],
    [
        ("heading", "3. Gerar o instalador Android pelo terminal"),
        ("body", "O APK é o instalador do Android. É necessário JDK 17 e Android SDK API 35. Não é preciso abrir o Android Studio. Se o APK já existir, vá para a instalação."),
        ("step", "1. Abra o PowerShell na pasta principal do projeto e configure Java e SDK:"),
        ("body", '$env:JAVA_HOME = "C:\\Program Files\\Eclipse Adoptium\\jdk-17.0.20.101-hotspot"'),
        ("body", '$env:PATH = "$env:JAVA_HOME\\bin;$env:PATH"'),
        ("body", '$env:ANDROID_HOME = "$env:LOCALAPPDATA\\Android\\Sdk"'),
        ("body", "$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME"),
        ("step", "2. Confira java -version (precisa mostrar 17) e Test-Path \"$env:ANDROID_HOME\\platforms\\android-35\" (precisa mostrar True). Se não tiver API 35, instale-a pelo sdkmanager e aceite as licenças."),
        ("step", "3. Execute estes comandos para limpar e compilar:"),
        ("body", ".\\gradlew.bat clean"),
        ("body", "if ($LASTEXITCODE -eq 0) { .\\gradlew.bat assembleDebug }"),
        ("step", "4. Aguarde BUILD SUCCESSFUL. Executar apenas .\\gradlew.bat mostra a ajuda e não gera o APK."),
        ("step", "5. O instalador fica em android/app/build/outputs/apk/debug/app-debug.apk. Transfira-o ao celular e abra o arquivo."),
        ("step", "6. Se solicitado, permita instalar apps desta fonte. Abra VORIQ e permita o microfone."),
        ("note", "Na primeira compilação, o Gradle baixa arquivos pela internet. Não precisa instalar Gradle separadamente."),
        ("heading", "4. Entrar no aplicativo"),
        ("step", "1. A primeira tela mostra a versão do app e o nome do Wi-Fi. Digite ID e senha. Depois do login, o app guarda as credenciais criptografadas no celular."),
        ("step", "2. O Android pode pedir permissão de Localização para revelar o nome do Wi-Fi. Em aparelhos antigos, ligue também Localização nas configurações do celular. Se o nome estiver indisponível, toque na mensagem do Wi-Fi para ver essa configuração; ainda é possível conectar."),
        ("step", "3. Toque em Entrar. O app procura o servidor automaticamente, sem pedir IP. Depois do login, abre a tela do comunicador. Toque em Contatos para abrir favoritos e pessoas online."),
    ],
    [
        ("heading", "5. Chamar e conversar"),
        ("step", "1. Na lista de pessoas online, toque na estrela para guardar ou remover um ID dos favoritos. Os favoritos ficam salvos no celular, inclusive quando estão offline."),
        ("step", "2. Toque em Chamar ao lado da pessoa desejada."),
        ("step", "3. Os dois celulares tocam dois bipes. A pessoa chamada toca em Aceitar para iniciar a chamada."),
        ("step", "4. Depois do aceite, segure Toque e segure para falar. Solte o botão para parar."),
        ("step", "5. Toque em Encerrar chamada quando terminar. Somente as duas pessoas da chamada ouvem o áudio."),
        ("note", "Para receber convites, o app precisa continuar conectado ao servidor na mesma rede Wi-Fi."),
        ("heading", "Receber chamadas com o app oculto"),
        ("step", "1. Permita as notificações do VORIQ. Deixe o app conectado e use o botão Início para ocultá-lo; não use Forçar parada."),
        ("step", "2. Na tela 1, toque em Ativar chamadas em segundo plano. No Android 14 ou mais novo, habilite também a opção de intents de tela inteira do VORIQ para permitir a abertura sobre o bloqueio."),
        ("step", "3. Com o celular desbloqueado, use Aceitar ou Recusar no alerta. Com a tela bloqueada e a permissão habilitada, o Android pode abrir a tela do convite."),
        ("note", "Economia de bateria, Wi-Fi desconectado ou Forçar parada podem interromper a conexão e os avisos."),
        ("heading", "Se algo nao funcionar"),
        ("body", "Servidor não encontrado: confirme mesmo Wi-Fi, servidor aberto e permissão do Firewall para Python em rede privada. O roteador deve permitir comunicação entre aparelhos; Wi-Fi de convidados pode bloquear."),
        ("body", "Conexão interrompida ao chamar: entre novamente e tente chamar alguém conectado. O terminal informa se o convite foi enviado ou se a pessoa estava offline/ocupada."),
        ("body", "Pessoa não aparece: ela precisa conectar o app ao mesmo servidor e Wi-Fi."),
        ("body", "Botão de falar cinza: aguarde a outra pessoa aceitar a chamada. O botão só ativa depois do aceite."),
        ("body", "Não consegue falar: habilite Microfone em Configurações > Aplicativos > VORIQ > Permissões e tente novamente."),
        ("body", "ID e senha não preencheram: digite-os novamente. O salvamento automático só ocorre depois de login bem-sucedido. Apagar os dados do app ou reinstalar remove as credenciais salvas."),
        ("heading", "Privacidade e limites"),
        ("body", "As credenciais guardadas no celular são criptografadas. Os favoritos guardam os IDs no aparelho. O servidor armazena hashes de senha em usuarios.json. A senha e o áudio não são criptografados durante o envio pela rede: use Wi-Fi privado e confiável, e não exponha as portas à internet."),
        ("body", "O computador servidor é necessário. A descoberta funciona somente no mesmo Wi-Fi acessível ao computador; não funciona entre redes diferentes nem pela rede móvel."),
        ("heading", "Identidade VORIQ"),
        ("body", "Marca VORIQ. Slogan: Sua voz. Sua conexão. Categoria: Comunicador Wi-Fi. A versão 1.12 permite chamadas privadas entre duas pessoas pela rede Wi-Fi local. Os atalhos de grupos e configurações são prévias; esses recursos, canais e áudio HD ainda não estão implementados."),
    ],
]


def make_pdf(page_streams):
    objects = [b""]

    def add(data):
        objects.append(data)
        return len(objects) - 1

    catalog = add(b"")
    tree = add(b"")
    regular = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    page_ids = []
    for stream in page_streams:
        stream_id = add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        page_ids.append(add(f"<< /Type /Page /Parent {tree} 0 R /MediaBox [0 0 {WIDTH} {HEIGHT}] /Resources << /Font << /F1 {regular} 0 R /F2 {bold} 0 R >> >> /Contents {stream_id} 0 R >>".encode()))
    objects[catalog] = f"<< /Type /Catalog /Pages {tree} 0 R >>".encode()
    objects[tree] = f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>".encode()
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, data in enumerate(objects[1:], 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + data + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode() + b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root {catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return pdf


for destination in DESTINATIONS:
    destination.parent.mkdir(parents=True, exist_ok=True)
    contents = make_pdf([build_page(sections, index) for index, sections in enumerate(pages, 1)])
    destination.write_bytes(contents)
    print(f"Gerado: {destination} ({len(contents)} bytes, {len(pages)} paginas)")
