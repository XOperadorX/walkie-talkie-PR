# Nextel Local

Protótipo de comunicação instantânea em grupo, inspirado no estilo walkie-talkie popularizado pela Nextel: mantenha o botão pressionado para falar e solte para encerrar. O projeto inclui servidor Python, página de cadastro e aplicativo Android (versão **1.1**, `versionCode 2`).

> **Importante:** este é um projeto independente e experimental. Ele não é produto oficial da Nextel ou Motorola, não usa rádio SMR, iDEN nem rede celular. A voz passa por Wi-Fi local e por um computador que precisa permanecer ligado. “FleetCall” aqui descreve a sala geral do protótipo; não é compatível com o serviço histórico FleetCall/Nextel.

## Como funciona

1. O computador executa o servidor e hospeda a página de cadastro.
2. Computador e celulares conectam-se ao mesmo roteador Wi-Fi.
3. Cada pessoa cria uma conta na página e usa seu ID e senha no Android.
4. Ao conectar, o app entra na sala geral. Pressione e segure **Toque e segure para falar**; solte para parar. Os demais aparelhos conectados recebem o áudio.

O áudio usa TCP na porta `5000`; a página e o cadastro usam TCP na porta `8080`. Não precisa de internet externa. A rede deve permitir que os aparelhos se comuniquem entre si.

## Iniciar no Windows

1. Instale Python 3.10 ou mais recente.
2. Execute `iniciar_servidor.bat`, ou abra o PowerShell nesta pasta e rode `python servidor/servidor_walkie.py`.
3. Se o Firewall perguntar, permita Python em redes privadas.
4. Abra no navegador o endereço mostrado no terminal, por exemplo `http://192.168.0.10:8080`.
5. Mantenha a janela do servidor aberta enquanto conversa.

As portas podem ser alteradas pelas variáveis `WALKIE_WEB_PORT` e `WALKIE_AUDIO_PORT`.

## Criar e instalar o app Android

1. Abra a pasta `android` no Android Studio e aguarde a sincronização do Gradle.
2. Escolha **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
3. O APK de depuração fica em `android/app/build/outputs/apk/debug/app-debug.apk`.
4. Baixe-o pela página do servidor ou transfira-o ao celular e confirme a instalação. Se solicitado, permita instalar apps desta fonte.
5. Abra **Nextel Local** e permita o microfone.

O app requer Android 8.0 (API 26) ou superior. O APK de depuração serve para instalação manual; publicação numa loja requer uma versão de lançamento assinada.

## Guia para celular

O [guia em PDF](docs/guia_do_usuario.pdf) explica os passos para pessoas iniciantes; uma cópia de entrega fica em `output/pdf/Nextel_Local_Guia_do_Usuario.pdf`. A fonte editável está em [docs/guia_do_usuario.md](docs/guia_do_usuario.md). Para recriar o PDF após editar o guia, execute `python docs/gerar_pdf.py`.

## Segurança e limites

- Use somente numa rede Wi-Fi privada e confiável. Senhas e áudio não têm criptografia de transporte; não exponha as portas à internet.
- `usuarios.json` é criado automaticamente e guarda hashes de senha. Faça cópia de segurança se precisar manter as contas.
- Existe uma sala geral, sem conversas privadas, histórico, disponibilidade contínua ou recuperação de senha.
- A versão 1.1 atualiza a identificação e as instruções de uso; não adiciona rádio celular nem infraestrutura de operadora.

## Referência histórica

FleetCall foi fundada em 1987 e adotou o nome Nextel em 1993. A Motorola desenvolveu iDEN (*Integrated Digital Enhanced Network*), lançada comercialmente pela Nextel nos EUA em 1996; o serviço Direct Connect popularizou a comunicação PTT nos anos 2000. SMR é a sigla de Specialized Mobile Radio; o nome Nextel evoca “next” (próximo) e “tel” (telefone). Esses marcos são contexto histórico, não descrição da tecnologia deste protótipo. Veja a [linha do tempo da Motorola Solutions](https://www.motorolasolutions.com/content/dam/msi/docs/products/broadband-ptt/wave-ebook.pdf) e o [registro da SEC sobre iDEN e Nextel](https://www.sec.gov/Archives/edgar/data/824169/000095013301502789/w53721aex99-1.htm).
