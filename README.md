# Nextel Local

Protótipo de comunicação por Wi-Fi com chamadas privadas e Push-to-Talk (PTT), inspirado na experiência de rádio da Nextel. O projeto reúne servidor Python, página de cadastro e aplicativo Android **versão 1.4** (`versionCode 5`).

> **Sobre o projeto:** Nextel Local é independente e experimental. Não é produto oficial da Nextel ou Motorola e não usa rádio SMR, iDEN nem rede de operadora. O computador servidor precisa ficar ligado. O celular encontra o servidor automaticamente na rede Wi-Fi local; não é preciso digitar o IP no aplicativo.

## Como conversar

1. Inicie o servidor no computador e mantenha-o aberto.
2. Conecte os celulares ao mesmo Wi-Fi do computador.
3. Cada pessoa cria uma conta na página do servidor. A **tela 1** do app pede ID e senha e mostra o nome do Wi-Fi. Depois de entrar, o aparelho guarda as credenciais criptografadas.
4. O app abre a **tela 2**, com pessoas disponíveis e favoritos. Toque na estrela para guardar ou remover um ID; os favoritos ficam salvos no celular.
5. Toque em **Chamar** ao lado da pessoa. O celular dela toca dois bipes; ela precisa aceitar.
6. Depois que aceitar, segure **Toque e segure para falar** enquanto fala e solte para parar. Só as duas pessoas da chamada recebem o áudio.
7. Toque em **Encerrar chamada** ao terminar ou em **Desconectar e voltar** para retornar à entrada.

A chamada toca enquanto o aplicativo da pessoa chamada está aberto em primeiro plano. Para receber convites, mantenha o app aberto e conectado. O servidor sinaliza convite e aceite, mas o transporte local ainda não criptografa voz nem senha: use uma rede privada confiável.

O Android pode solicitar permissão de localização para revelar o nome da rede Wi-Fi. O app usa essa permissão somente para exibir o nome; se ela for negada, a conexão automática continua disponível, mas o nome pode aparecer como indisponível.

## Iniciar o servidor no Windows

1. Instale Python 3.10 ou mais recente.
2. Execute `iniciar_servidor.bat`, ou abra o PowerShell na pasta do projeto e execute:

```powershell
python servidor/servidor_walkie.py
```

3. Se o Firewall do Windows perguntar, permita Python em **redes privadas**.
4. Para abrir o cadastro, use no navegador do celular ou computador o endereço HTTP impresso no terminal, por exemplo `http://192.168.0.10:8080`. Esse IP serve para a página de cadastro/download; **não precisa digitá-lo no aplicativo**.
5. Mantenha a janela aberta durante as conversas.

O servidor usa TCP `5000` para chamadas, UDP `5001` para descoberta automática e TCP `8080` para cadastro/download. Todos os aparelhos devem poder se comunicar entre si no Wi-Fi. Redes de convidados ou isolamento de clientes podem bloquear essa comunicação.

As portas podem ser personalizadas com `WALKIE_WEB_PORT`, `WALKIE_AUDIO_PORT` e `WALKIE_DISCOVERY_PORT`.

O site é dividido em `web/inicio.html`, `web/cadastro.html` e `web/apk.html`, todas com o mesmo menu. `web/index.html` continua disponível como página inicial para manter o endereço `/` e o caminho `/index.html` funcionando.

## Criar e instalar o app Android pelo terminal

Não é preciso abrir o Android Studio. O computador precisa de JDK 17 e Android SDK com plataforma API 35. No PowerShell, na pasta principal do projeto, configure o Java e o local padrão do SDK:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
java -version
Test-Path "$env:ANDROID_HOME\platforms\android-35"
```

Essas variáveis valem para esta janela do PowerShell. Abra outra janela e repita os comandos se necessário. Confirme Java 17 e resultado `True` no último comando. Se o SDK estiver em outro caminho, ajuste `ANDROID_HOME`. Se API 35 não estiver instalada, use `sdkmanager`:

```powershell
$env:PATH = "$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"
sdkmanager --licenses
sdkmanager "platforms;android-35" "build-tools;34.0.0"
```

Aceite as licenças. Se `sdkmanager` não for encontrado, instale as [Android Command-line Tools](https://developer.android.com/tools/sdkmanager) ou corrija o caminho do SDK.

Execute a compilação no terminal:

```powershell
.\gradlew.bat clean
if ($LASTEXITCODE -eq 0) { .\gradlew.bat assembleDebug }
```

Não execute somente `.\gradlew.bat`: sem uma tarefa, o Gradle mostra a ajuda e não cria o APK. Na primeira compilação, o Wrapper baixa Gradle 8.9, então o computador precisa de internet. O APK de depuração será criado em `android/app/build/outputs/apk/debug/app-debug.apk`. Transfira-o ao celular, instale e permita o microfone.

O app requer Android 8.0 (API 26) ou mais novo. Para publicar numa loja é necessário gerar uma versão de lançamento assinada.

## Guia para iniciantes

O [guia em PDF](docs/guia_do_usuario.pdf) explica a instalação e o uso pelo celular. A fonte editável fica em [docs/guia_do_usuario.md](docs/guia_do_usuario.md). Após atualizar a fonte, regenere as cópias com:

```powershell
python docs/gerar_pdf.py
```

O script atualiza `docs/guia_do_usuario.pdf` e `output/pdf/Nextel_Local_Guia_do_Usuario.pdf`.

## Privacidade e limites

- ID e senha ficam criptografados no armazenamento privado do app após o primeiro login bem-sucedido. Ao limpar os dados do app ou reinstalá-lo, será necessário digitá-los novamente.
- O servidor guarda somente hashes das senhas em `usuarios.json`.
- O tráfego de senha e áudio não usa criptografia de transporte. Use uma rede confiável e não exponha as portas à internet.
- O servidor encaminha áudio apenas entre participantes de uma chamada aceita; não há sala geral, histórico ou notificações quando o app está fechado.
- Os favoritos guardam somente IDs no aparelho e continuam visíveis mesmo quando esses contatos estão offline.
- A descoberta automática funciona na mesma rede Wi-Fi acessível ao computador servidor. Não funciona através de redes diferentes ou da rede móvel.

## Referência histórica

FleetCall foi fundada em 1987 e adotou o nome Nextel em 1993. A Motorola desenvolveu iDEN (*Integrated Digital Enhanced Network*), lançada comercialmente pela Nextel nos EUA em 1996; o serviço Direct Connect popularizou PTT nos anos 2000. SMR significa *Specialized Mobile Radio*. Esses marcos inspiram a interação do protótipo, que opera somente por Wi-Fi local. Veja a [linha do tempo da Motorola Solutions](https://www.motorolasolutions.com/content/dam/msi/docs/products/broadband-ptt/wave-ebook.pdf) e o [registro da SEC sobre iDEN e Nextel](https://www.sec.gov/Archives/edgar/data/824169/000095013301502789/w53721aex99-1.htm).
