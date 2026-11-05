# Walkie-Talkie em rede local

Projeto de comunicação por voz em uma sala geral, com servidor Python, página web de cadastro e aplicativo Android. O servidor e todos os celulares devem estar ligados ao mesmo roteador Wi-Fi. A voz trafega pela rede local e não depende de internet externa.

## Estrutura

- `servidor/servidor_walkie.py`: servidor HTTP, cadastro e transmissão de áudio.
- `web/index.html`: página de cadastro e download.
- `android/`: projeto Android Studio em Kotlin.
- `docs/guia_do_usuario.pdf`: instruções ilustradas em texto simples para instalação e uso.
- `usuarios.json`: criado automaticamente na primeira conta; contém hashes de senha, nunca a senha em texto aberto.

## 1. Iniciar o servidor no Windows

1. Instale Python 3.10 ou mais recente.
2. Dê dois cliques em `iniciar_servidor.bat`, ou abra o PowerShell nesta pasta do projeto.
3. No PowerShell, execute `python servidor/servidor_walkie.py`.
4. Permita o Python na rede privada quando o Firewall do Windows perguntar.
5. Copie o endereço `http://IP:8080` mostrado no terminal e abra-o no computador ou celular.
6. Deixe a janela aberta enquanto usar o walkie-talkie.

As portas padrão são TCP `8080` para a página e TCP `5000` para voz. Podem ser alteradas pelas variáveis `WALKIE_WEB_PORT` e `WALKIE_AUDIO_PORT`. Para acessar pelo Wi-Fi, o firewall do computador precisa permitir essas portas na rede privada.

## 2. Criar uma conta

Na página web, informe um nome e uma senha de pelo menos 8 caracteres. Guarde o ID exibido após o cadastro: o app pede o ID e a senha. Os dados ficam no arquivo `usuarios.json` no computador servidor.

## 3. Gerar e instalar o APK

O APK não é incluído pronto. Gere-o com Android Studio:

1. Abra a pasta `android` no Android Studio e aguarde a sincronização do Gradle.
2. Selecione **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
3. O APK de depuração será criado em `android/app/build/outputs/apk/debug/app-debug.apk`.
4. Para disponibilizá-lo na página, reinicie/atualize o servidor se necessário e abra `http://IP:8080/download`.
5. No celular, abra o APK e permita a instalação solicitada pelo Android. Permita também o uso do microfone ao abrir o aplicativo.

O app é configurado para Android 8.0 (API 26) ou superior. O APK de depuração é para instalação manual; uma publicação na Play Store requer assinatura de lançamento.

## 4. Conectar e falar

No app, informe o IP do computador exibido no terminal, o ID e a senha. Toque em **Conectar**. Para transmitir, mantenha **Segure para falar** pressionado; solte para encerrar a fala. Todos os clientes autenticados recebem a voz na sala geral.

## Se algo não funcionar

- Confira se computador e celulares estão no mesmo Wi-Fi e se o roteador permite comunicação entre aparelhos (algumas redes de convidados bloqueiam isso).
- Confirme o IP no terminal; ele pode mudar quando o roteador reinicia.
- Autorize `python.exe` no Firewall do Windows para redes privadas ou crie regras TCP para as portas 8080 e 5000.
- Se a página abre mas o áudio não conecta, verifique a porta 5000 e o IP no app.
- Se o botão de fala não funcionar, habilite a permissão de microfone nas configurações do Android.
- A voz e a senha trafegam sem criptografia de transporte. Use somente em uma rede confiável; não exponha as portas à internet.

## Limites desta versão

A versão atual oferece uma sala geral, sem chamadas privadas, histórico, criptografia de áudio ou recuperação de senha. É um protótipo para rede local. O servidor é o retransmissor do áudio; aparelhos não enviam voz diretamente uns aos outros.
