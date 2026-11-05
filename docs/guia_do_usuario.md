# Guia do Walkie-Talkie Local

## O que você precisa

- Um computador com Python 3.10 ou mais novo.
- Um celular Android 8.0 ou mais novo.
- Todos os aparelhos conectados ao mesmo Wi-Fi.
- Uma rede privada confiável. Não compartilhe o servidor pela internet.

## A. Ligar o servidor

1. No computador, abra a pasta do projeto.
2. Dê dois cliques no arquivo `iniciar_servidor.bat`. Se preferir, abra o PowerShell dentro dessa pasta.
3. No PowerShell, digite `python servidor/servidor_walkie.py` e pressione Enter.
4. Se o Windows perguntar sobre o Firewall, permita o acesso em redes privadas.
5. Anote o endereço web e o IP impressos no terminal. Exemplo: `http://192.168.0.10:8080`.
6. Não feche o PowerShell durante a conversa.

## B. Criar seu acesso

1. Abra o endereço web em um navegador conectado ao mesmo Wi-Fi.
2. Digite seu nome e crie uma senha com pelo menos 8 caracteres.
3. Pressione **Cadastrar**.
4. Anote o ID apresentado. Você usará o ID e a senha no aplicativo.

## C. Gerar e instalar o aplicativo

O projeto contém os arquivos fonte do Android. Para criar o arquivo de instalação:

1. Instale o Android Studio no computador.
2. Abra nele a pasta `android` deste projeto.
3. Aguarde o Android Studio sincronizar o projeto.
4. No menu, escolha **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
5. Quando terminar, o Android Studio mostrará a opção para localizar o APK. O caminho dentro do projeto é `android/app/build/outputs/apk/debug/app-debug.apk`.
6. Volte à página do servidor e toque em **Baixar APK**, ou copie o APK para o celular por cabo/arquivo.
7. Abra o arquivo no celular. Se o Android pedir, permita instalar aplicativos desta fonte e confirme **Instalar**.
8. Abra Walkie-Talkie Local e permita o microfone.

## D. Conectar e conversar

1. No campo de IP do app, digite o endereço do computador, sem `http://` e sem `:8080`. Exemplo: `192.168.0.10`.
2. Digite seu ID e sua senha.
3. Toque em **Conectar**.
4. Para falar, mantenha o botão **Segure para falar** pressionado. Fale perto do microfone.
5. Solte o botão para terminar. Os outros aparelhos conectados recebem o áudio.
6. Para sair, toque em **Desconectar**.

## Quando não conectar

- Verifique se os aparelhos estão no mesmo Wi-Fi. Redes de convidados podem impedir que aparelhos se encontrem.
- Confira se o servidor continua rodando e se você digitou o IP correto.
- Se o Windows mostrar um alerta do Firewall, permita Python na rede privada. A página usa a porta 8080 e o áudio usa a porta 5000.
- Verifique a permissão de microfone em **Configurações > Aplicativos > Walkie-Talkie Local > Permissões**.
- O IP pode mudar depois que o roteador reiniciar; use o IP atual mostrado no terminal.
- Se a tela web informar que o APK ainda não existe, gere-o no Android Studio conforme a seção C.

## Cuidados

O áudio e a senha circulam sem criptografia de transporte. Use apenas em uma rede Wi-Fi em que você confia e não encaminhe as portas do roteador para a internet. O arquivo `usuarios.json` guarda os cadastros com hashes de senha; mantenha uma cópia de segurança se precisar preservar as contas.
