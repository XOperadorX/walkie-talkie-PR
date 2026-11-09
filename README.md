# VORIQ

## Sua voz. Sua conexão.

Comunicador Wi-Fi para chamadas privadas entre pessoas conectadas à mesma rede local. O computador que executa o servidor precisa permanecer ligado durante o uso.

Aplicativo experimental de comunicação por voz em uma rede Wi-Fi local. O projeto reúne um servidor Python, páginas Web para criar e administrar contas e um aplicativo Android com chamadas privadas e botão Push-to-Talk (PTT).

VORIQ é um projeto independente. Ele não usa rede de operadora; os celulares e o servidor precisam estar no mesmo Wi-Fi.

## Identidade

- **Marca:** VORIQ
- **Slogan:** Sua voz. Sua conexão.
- **Categoria:** Comunicador Wi-Fi
- **Autor:** Moises20XX
- **Empresa:** MMQuaseTudo
- **Cores:** azul-noturno, azul digital e ciano
- **Símbolo:** letra V com ondas de rádio

## O que está incluído

- `servidor/servidor_walkie.py`: autenticação, chamadas, descoberta na rede local, páginas Web e download do APK.
- `web/index.html` e `web/inicio.html`: página inicial e instruções rápidas.
- `web/cadastro.html`: criação de contas para os usuários do aplicativo.
- `web/adm_cadastro.html`: tela para adicionar, editar nome ou senha e excluir contas.
- `web/apk.html`: página para baixar o APK compilado.
- `android/`: aplicativo Android.
- `iniciar_servidor.bat`: atalho para iniciar o servidor no Windows.
- `docs/guia_do_usuario.pdf` e `docs/guia_do_usuario.md`: guia de instalação e uso.

## Requisitos

### Para executar o servidor

- Windows com Python 3.10 ou mais recente.
- Computador e celulares conectados à mesma rede Wi-Fi, sem isolamento entre os aparelhos.

### Para compilar o aplicativo Android

- JDK 17.
- Android SDK com a plataforma Android API 35.
- Acesso à internet na primeira compilação para o Gradle baixar o Wrapper e as dependências.

O APK requer Android 8.0 (API 26) ou mais recente.

## Iniciar o servidor no Windows

Abra um terminal na pasta do projeto e execute:

```powershell
python servidor/servidor_walkie.py
```

Também é possível iniciar com duplo clique em `iniciar_servidor.bat`. Para usar a administração de contas, inicie pelo PowerShell como descrito na seção [Administrar contas](#administrar-contas). O atalho `.bat` usa os valores de ambiente que já existirem no processo que o iniciou.

Na inicialização, o terminal informa o endereço da página, por exemplo `http://192.168.0.10:8080`. Permita o Python no Firewall do Windows em **redes privadas**, caso o Windows solicite. Mantenha a janela do servidor aberta enquanto o aplicativo estiver em uso.

O servidor usa estas portas padrão:

| Serviço | Porta e protocolo | Uso |
| --- | --- | --- |
| Páginas Web e download | `8080/TCP` | Cadastro, administração e download do APK |
| Chamadas e áudio | `5000/TCP` | Login, convites, controles e transmissão de voz |
| Descoberta automática | `5001/UDP` | Localizar o servidor na mesma rede |

As portas podem ser alteradas pelas variáveis `WALKIE_WEB_PORT`, `WALKIE_AUDIO_PORT` e `WALKIE_DISCOVERY_PORT`. Se alterar as portas, libere os novos valores no firewall e mantenha a configuração coerente com o aplicativo.

## Criar uma conta e conversar

1. Inicie o servidor e conecte os celulares à mesma rede Wi-Fi do computador.
2. No navegador, abra o endereço exibido pelo servidor e toque em **Criar acesso**.
3. Informe um nome e crie uma senha com 8 a 128 caracteres. Guarde o ID gerado e a senha.
4. Compile e instale o APK conforme a seção [Compilar o aplicativo Android](#compilar-o-aplicativo-android).
5. No aplicativo, entre com seu ID e senha. A permissão de microfone é necessária para falar. A permissão de localização é solicitada para que o Android possa revelar o nome da rede Wi-Fi; se for negada, a conexão automática ainda pode funcionar.
6. Escolha uma pessoa que esteja online e toque em **Chamar**. A pessoa chamada precisa estar com o aplicativo aberto e aceitar o convite.
7. Depois do aceite, segure **Toque e segure para falar** enquanto fala e solte para parar. O áudio é encaminhado somente à outra pessoa da chamada aceita.
8. Use **Encerrar chamada** para finalizar ou **Desconectar e voltar** para sair da conexão.

O aplicativo mostra a lista de pessoas conectadas e permite guardar IDs como favoritos no próprio celular. Favoritos permanecem salvos mesmo quando a pessoa está offline. Cada usuário deve usar seu próprio ID; entrar com o mesmo ID em outro aparelho substitui a sessão anterior.

## Administrar contas

A administração fica disponível em `adm_cadastro.html` e exige uma senha definida pelo responsável pelo servidor. No PowerShell, defina a variável e inicie o servidor na mesma janela:

```powershell
$env:WALKIE_ADMIN_PASSWORD = "substitua-por-uma-senha-forte"
python servidor/servidor_walkie.py
```

Abra o endereço exibido pelo servidor seguido de `/adm_cadastro.html`, por exemplo `http://192.168.0.10:8080/adm_cadastro.html`. Quando o navegador solicitar as credenciais, use o usuário `admin` e a senha configurada em `WALKIE_ADMIN_PASSWORD`.

Na tela administrativa é possível:

- adicionar um cadastro com nome e senha;
- editar o nome mantendo o ID atual;
- trocar a senha informando uma nova senha no campo correspondente, ou manter a senha deixando-o em branco;
- excluir um cadastro.

Sem `WALKIE_ADMIN_PASSWORD`, as operações administrativas ficam desabilitadas. A tela pode continuar acessível, mas não poderá listar nem alterar usuários.

## Compilar o aplicativo Android

No PowerShell, na pasta principal do projeto, configure o Java e o caminho do SDK. Ajuste o caminho do JDK se a instalação local estiver em outro lugar:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
java -version
Test-Path "$env:ANDROID_HOME\platforms\android-35"
```

Confirme que o Java é a versão 17 e que o último comando retorna `True`. Se o Android SDK estiver em outro diretório, ajuste `ANDROID_HOME`. Para instalar a plataforma 35 usando as Android Command-line Tools:

```powershell
$env:PATH = "$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"
sdkmanager --licenses
sdkmanager "platforms;android-35" "build-tools;34.0.0"
```

Aceite as licenças exibidas. Se `sdkmanager` não for encontrado, instale as [Android Command-line Tools](https://developer.android.com/tools/sdkmanager) ou ajuste o caminho para a pasta que contém o executável.

Compile o APK de depuração:

```powershell
.\gradlew.bat clean
if ($LASTEXITCODE -eq 0) { .\gradlew.bat assembleDebug }
```

Não execute somente `.\gradlew.bat` sem uma tarefa: isso mostra a ajuda do Gradle e não compila o aplicativo. Quando a compilação terminar com `BUILD SUCCESSFUL`, o APK estará em `android/app/build/outputs/apk/debug/app-debug.apk`. Transfira esse arquivo ao celular, instale-o e permita a instalação de aplicativos dessa fonte, se o Android solicitar.

Depois que o APK existir nesse caminho, a página **APK** do site permite baixá-lo. Se ainda não foi compilado, o servidor informa que o APK não está disponível. O projeto gera um APK de depuração; para distribuir por uma loja, é necessário preparar e assinar uma versão de lançamento.

## Dados e configurações do servidor

O servidor cria `usuarios.json` na pasta principal do projeto. As senhas das contas são salvas como hashes PBKDF2-HMAC-SHA256 com salt aleatório; o arquivo não guarda as senhas em texto puro. Faça cópias de segurança desse arquivo para preservar os cadastros.

As variáveis de ambiente disponíveis são:

| Variável | Valor padrão | Finalidade |
| --- | --- | --- |
| `WALKIE_WEB_PORT` | `8080` | Porta TCP do site e do download |
| `WALKIE_AUDIO_PORT` | `5000` | Porta TCP de chamadas e áudio |
| `WALKIE_DISCOVERY_PORT` | `5001` | Porta UDP de descoberta automática |
| `WALKIE_DATA_FILE` | `usuarios.json` na pasta do projeto | Caminho alternativo para o arquivo de contas |
| `WALKIE_ADMIN_PASSWORD` | não definido | Senha necessária para administrar contas |

As variáveis definidas no PowerShell valem para aquela janela e para os processos iniciados nela. Para manter uma configuração entre sessões, configure as variáveis no Windows antes de iniciar o servidor.

## Guia para iniciantes

O [guia do usuário em PDF](docs/guia_do_usuario.pdf) explica a instalação e o uso pelo celular. O arquivo editável é [docs/guia_do_usuario.md](docs/guia_do_usuario.md). Para gerar novamente as cópias do PDF após editar o guia:

```powershell
python docs/gerar_pdf.py
```

O script salva `docs/guia_do_usuario.pdf` e `output/pdf/VORIQ_Guia_do_Usuario.pdf`.

## Limitações e segurança

- O servidor e os celulares precisam estar na mesma rede Wi-Fi, com comunicação local permitida. Redes de convidados podem bloquear a descoberta ou o tráfego entre aparelhos.
- Mantenha o aplicativo aberto e conectado para receber convites. Não há notificações quando o aplicativo está fechado.
- A voz só é encaminhada entre as duas pessoas de uma chamada aceita; não há sala geral nem histórico de áudio.
- O servidor usa HTTP sem TLS. A senha administrativa e os dados enviados pelo site não são protegidos durante o transporte. Use somente uma rede privada confiável, escolha uma senha administrativa forte e não exponha as portas do servidor à internet.
- A senha e o áudio enviados pelo aplicativo também não têm criptografia de transporte. Use somente uma rede confiável e não encaminhe as portas do roteador para a internet.
- O aplicativo guarda as credenciais criptografadas no armazenamento privado do aparelho depois de um login bem-sucedido. Se os dados do aplicativo forem apagados ou ele for reinstalado, será preciso informar ID e senha novamente.
- Se a conexão cair ou uma pessoa estiver offline/ocupada, confira a mensagem no aplicativo e os registros exibidos no terminal do servidor.

## Solução de problemas

- **A página não abre no celular:** confirme que o celular e o computador estão no mesmo Wi-Fi, use o endereço exibido pelo servidor e permita Python no Firewall do Windows para redes privadas.
- **O aplicativo não encontra o servidor:** confira se UDP `5001` está liberado e se o roteador permite comunicação entre aparelhos conectados. Redes de convidados podem impedir isso.
- **O login falha:** confira o ID e a senha. As contas ficam no `usuarios.json` usado pelo servidor; se `WALKIE_DATA_FILE` estiver configurada, confira o caminho alternativo.
- **A tela administrativa pede senha repetidamente ou não carrega os dados:** inicie o servidor com `WALKIE_ADMIN_PASSWORD` definida na mesma janela e use usuário `admin` com essa senha.
- **A página APK diz que o arquivo não existe:** compile o projeto Android e confirme que `android/app/build/outputs/apk/debug/app-debug.apk` foi criado.
- **O áudio não funciona:** permita o uso do microfone, mantenha os dois aplicativos abertos e conectados e confirme que o TCP `5000` está permitido na rede local.

## Versão atual

O aplicativo Android está configurado como versão **1.9** (`versionCode 10`), com `compileSdk` e `targetSdk` 35 e versão mínima Android 8.0 (API 26). A tela principal apresenta o botão PTT e atalhos; **Contatos** abre favoritos e pessoas online. Esta versão mantém chamadas privadas entre duas pessoas e descoberta automática do servidor. Grupos, canais e áudio HD das imagens conceituais ainda não estão implementados.
