# Guia do Nextel Local para celular

Este guia acompanha o Nextel Local versão **1.4**. Ele ensina a instalar, conectar e fazer uma chamada privada pelo celular. O aplicativo usa o Wi-Fi local e um computador servidor. Não é um rádio Nextel original e não se conecta às redes SMR, iDEN ou de operadora.

## O que você precisa

- Um computador Windows com Python 3.10 ou mais novo.
- Um celular Android 8.0 ou mais novo para cada pessoa.
- Todos conectados à mesma rede Wi-Fi privada. O roteador precisa permitir que os aparelhos se comuniquem.
- O servidor ligado durante a conversa.

## 1. Ligar o servidor

1. No computador, abra a pasta do projeto.
2. Dê dois cliques em `iniciar_servidor.bat`. Ou abra o PowerShell nessa pasta e execute `python servidor/servidor_walkie.py`.
3. Se o Firewall do Windows perguntar, permita Python em redes privadas.
4. Deixe a janela do servidor aberta.

O terminal mostra um endereço, como `http://192.168.0.10:8080`. Você vai usar esse endereço somente para abrir a página de cadastro ou baixar o instalador. **Não precisa informar o IP no aplicativo.**

O site tem três páginas no menu: **Início**, **Criar acesso** e **APK**. Use **Criar acesso** para fazer sua conta e **APK** para baixar o instalador.

O servidor usa TCP 8080 para a página, TCP 5000 para chamadas e UDP 5001 para localizar automaticamente o servidor. Se o firewall solicitar acesso em rede privada, permita.

## 2. Criar seu ID e senha

1. No celular ou computador conectado ao mesmo Wi-Fi, abra o endereço mostrado no terminal.
2. Digite seu nome e crie uma senha com pelo menos 8 caracteres.
3. Toque em **Cadastrar**.
4. Anote o ID que aparece na página e guarde-o com a senha. Cada participante precisa criar a própria conta.

## 3. Gerar e instalar o aplicativo pelo terminal

O APK é o instalador do Android. Para criá-lo, o computador precisa de JDK 17 e Android SDK API 35. Não é preciso abrir o Android Studio. Se você já gerou o APK, pule para o passo 7.

1. Abra o PowerShell na pasta principal do projeto.
2. Configure o JDK 17 e o caminho padrão do SDK. Se esses programas estiverem em outros locais, ajuste os caminhos.

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
java -version
Test-Path "$env:ANDROID_HOME\platforms\android-35"
```

3. Confirme que `java -version` mostra Java 17. Se o último comando mostrar `False` e `cmdline-tools\latest\bin` existir dentro do SDK, instale a plataforma:

```powershell
$env:PATH = "$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"
sdkmanager --licenses
sdkmanager "platforms;android-35" "build-tools;34.0.0"
```

Aceite as licenças. Se `sdkmanager` não for encontrado, instale as Android Command-line Tools ou corrija `ANDROID_HOME`. A pasta do SDK contém subpastas como `platforms`, `build-tools` e `platform-tools`.

4. Compile pelo terminal:

```powershell
.\gradlew.bat clean
if ($LASTEXITCODE -eq 0) { .\gradlew.bat assembleDebug }
```

5. Aguarde a mensagem `BUILD SUCCESSFUL`. Executar apenas `.\gradlew.bat` mostra a ajuda e não gera o instalador.
6. O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`.
7. Transfira o APK para o celular e abra o arquivo para instalar. Se o Android perguntar, permita instalar aplicativos desta fonte. Abra **Nextel Local** e permita o uso do microfone.

Na primeira compilação, o Gradle Wrapper baixa Gradle 8.9 pela internet. Não precisa instalar Gradle separadamente.

## 4. Conectar e fazer chamada

1. Confirme que o servidor está ligado e que os celulares usam o mesmo Wi-Fi do computador.
2. Abra o Nextel Local. A **tela 1** mostra o nome do Wi-Fi e os campos de ID e senha. Na primeira vez, digite seus dados. Depois de entrar com sucesso, o app salva ID e senha criptografados no celular.
3. O Android pode pedir permissão de localização para mostrar o nome do Wi-Fi. O aplicativo usa essa permissão somente para ler o nome da rede; não calcula nem registra a localização do aparelho. Se não permitir, ainda pode conectar, mas talvez o nome da rede não apareça.
4. Toque em **Entrar**. O aplicativo procura o servidor automaticamente, sem pedir IP. Quando a conexão for aceita, abre a **tela 2**.
5. A tela 2 mostra os favoritos e as pessoas online. Toque na estrela ao lado de um ID para adicioná-lo ou removê-lo dos favoritos. A lista de favoritos fica salva no celular, mesmo quando a pessoa está offline.
6. Toque em **Chamar** ao lado da pessoa desejada. O celular dela toca dois bipes e mostra o pedido. Ela deve tocar em **Aceitar**. Mantenha o app dela aberto para receber o convite.
7. Depois que a chamada for aceita, qualquer um dos dois pode segurar **Toque e segure para falar**, falar e soltar o botão para parar.
8. Toque em **Encerrar chamada** para terminar. A voz só é enviada entre as duas pessoas que aceitaram participar.
9. Toque em **Desconectar e voltar** para encerrar a conexão e retornar à tela 1.

Esse modo de falar é chamado Push-to-Talk (PTT): pressione e segure para falar, solte para parar. O convite e o aceite precisam acontecer antes do áudio.

## Se algo não funcionar

- **Servidor não encontrado:** confira se o computador e o celular estão no mesmo Wi-Fi, se o servidor continua aberto e se o firewall permite Python em rede privada.
- **Conecta à página, mas o app não encontra o servidor:** o roteador pode bloquear a comunicação entre aparelhos. Redes de convidados costumam ter esse bloqueio. O servidor precisa receber UDP 5001 e TCP 5000 em rede privada.
- **Pessoa não aparece na lista:** ela precisa estar conectada no app ao mesmo servidor e Wi-Fi.
- **Botão para falar continua cinza:** durante o convite, o app mostra “Aguarde o aceite para falar”. O botão só fica ativo depois que a outra pessoa aceita; isso evita transmitir áudio antes da chamada começar.
- **Não ouviu o bip ou não recebeu o convite:** mantenha o aplicativo aberto em primeiro plano e conectado. O protótipo ainda não mostra notificações quando o app está fechado.
- **Nome do Wi-Fi não aparece:** permita a leitura da localização para que o Android revele o nome da rede. O aplicativo usa essa permissão somente para mostrar o nome do Wi-Fi; sem ela, a conexão automática ainda pode funcionar.
- **Não consegue falar:** habilite o microfone em **Configurações > Aplicativos > Nextel Local > Permissões**. Encerre a chamada e conecte novamente.
- **ID/senha não foram preenchidos:** o salvamento ocorre depois de um login bem-sucedido. Se os dados do app forem apagados ou ele for reinstalado, digite-os outra vez.
- **Não consegue instalar:** confirme que o APK foi gerado em `android/app/build/outputs/apk/debug/app-debug.apk` e permita instalar apps desta fonte.

## Privacidade e limites

Use apenas numa rede Wi-Fi privada e confiável. O app guarda ID e senha criptografados no aparelho, mas senha e voz não têm criptografia enquanto viajam pela rede local. Não encaminhe as portas do roteador para a internet. Os cadastros ficam em `usuarios.json` no computador em formato de hash de senha.

O servidor e os celulares precisam estar ligados e na mesma rede local acessível. O aplicativo não liga pela rede celular, não usa SMR ou iDEN e não conversa com aparelhos Nextel antigos. O nome Nextel e os marcos históricos são apenas inspiração; este projeto não tem vínculo oficial com Nextel ou Motorola.

### Contexto histórico

FleetCall começou em 1987 e adotou o nome Nextel Communications em 1993. A Motorola criou a tecnologia iDEN (*Integrated Digital Enhanced Network*), lançada comercialmente pela Nextel nos EUA em 1996. SMR significa *Specialized Mobile Radio*. Nos anos 2000, o Direct Connect popularizou o estilo Push-to-Talk. Nextel evoca as palavras inglesas *next* (próximo) e *tel* (telefone). O protótipo atual reproduz o gesto de pressionar para falar usando Wi-Fi local.

## Atualização deste guia

A fonte deste manual é `docs/guia_do_usuario.md`. Depois de atualizar o texto, gere os PDFs com `python docs/gerar_pdf.py`.
