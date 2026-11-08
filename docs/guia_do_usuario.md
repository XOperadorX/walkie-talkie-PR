# Guia do Nextel Local para celular

Este guia ensina a entrar na sala de voz. O Nextel Local é um protótipo independente: funciona por Wi-Fi local com um computador servidor. Não é um rádio Nextel original e não conecta às redes SMR, iDEN ou celular.

## O que você precisa

- Um computador Windows com Python 3.10 ou mais novo.
- Um celular Android 8.0 ou mais novo para cada pessoa.
- Todos no mesmo Wi-Fi; o roteador precisa permitir a comunicação entre aparelhos.
- Uma rede privada confiável.

## 1. Ligar o servidor

1. No computador, abra a pasta do projeto.
2. Dê dois cliques em `iniciar_servidor.bat`. Outra opção: abra o PowerShell nessa pasta e execute `python servidor/servidor_walkie.py`.
3. Se o Firewall do Windows perguntar, permita o Python em redes privadas.
4. Anote o endereço impresso, por exemplo `http://192.168.0.10:8080`. Esse número é o endereço do computador na rede.
5. Deixe a janela aberta durante a conversa.

## 2. Criar uma conta

1. No celular ou computador conectado ao mesmo Wi-Fi, abra o endereço anotado no navegador.
2. Digite seu nome e crie uma senha com pelo menos 8 caracteres.
3. Toque em **Cadastrar**.
4. Anote o ID apresentado e guarde-o com a senha. Cada participante cria sua própria conta.

## 3. Instalar o aplicativo

O arquivo APK é o instalador do Android. Primeiro, alguém precisa gerar o APK no computador:

1. Instale e abra o Android Studio.
2. Abra a pasta `android` deste projeto e espere a sincronização terminar.
3. No menu, escolha **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
4. O arquivo criado fica em `android/app/build/outputs/apk/debug/app-debug.apk`.
5. Na página do servidor, toque em **Baixar APK** ou transfira esse arquivo ao celular.
6. Abra o APK. Se o Android perguntar, permita instalar aplicativos desta fonte e confirme **Instalar**.
7. Abra **Nextel Local** e permita o acesso ao microfone.

## 4. Entrar na sala e falar

1. Confirme que o servidor segue aberto e que o celular está no mesmo Wi-Fi.
2. No campo do IP, digite apenas o endereço do computador. Exemplo: `192.168.0.10`. Não inclua `http://` nem `:8080`.
3. Digite seu ID e sua senha.
4. Toque em **Conectar**. Aguarde a mensagem **Conectado à sala geral**.
5. Para falar, toque e mantenha pressionado **Toque e segure para falar**. Fale perto do microfone.
6. Solte o botão para encerrar. Todos os outros celulares conectados à sala recebem sua voz.
7. Ao terminar, toque em **Desconectar**.

Esse jeito de conversar é chamado Push-to-Talk (PTT): pressione para falar, solte para parar. A sala geral funciona como uma chamada de grupo. Neste protótipo, todos compartilham a mesma sala.

## Se algo não funcionar

- **Não conecta:** confirme que todos estão no mesmo Wi-Fi, que o servidor está aberto e que o IP está correto. O IP pode mudar se o roteador reiniciar.
- **Página abre, mas o app não conecta:** o roteador pode bloquear aparelhos entre si. No Firewall, permita o Python em rede privada. A página usa TCP 8080 e o áudio TCP 5000.
- **Não consegue falar:** habilite o microfone em **Configurações > Aplicativos > Nextel Local > Permissões**. Reconecte depois.
- **Não encontra o instalador:** gere o APK no Android Studio seguindo a seção 3.
- **Servidor parou:** abra `iniciar_servidor.bat` de novo e use o IP que aparecer.

## Privacidade e limites

Use apenas numa rede confiável. A senha e o áudio não têm criptografia durante o transporte. Não encaminhe as portas do roteador para a internet. Os cadastros ficam em `usuarios.json` no computador.

O nome Nextel e os marcos históricos apresentados no material identificam a inspiração do projeto. Não há vínculo oficial com Nextel ou Motorola. O app não usa rádio SMR ou iDEN, não usa rede de operadora, e depende do computador-servidor e do Wi-Fi local. “FleetCall” descreve aqui a sala geral do protótipo, não um serviço compatível com o FleetCall histórico.

### Contexto histórico

A empresa começou em 1987 como FleetCall e adotou o nome Nextel Communications em 1993. A Motorola criou a tecnologia iDEN (*Integrated Digital Enhanced Network*), que a Nextel lançou comercialmente nos EUA em 1996. SMR significa Specialized Mobile Radio, categoria de serviço de rádio móvel especializado. Nos anos 2000, o Direct Connect ficou conhecido pelo estilo de comunicação Push-to-Talk. O nome Nextel evoca as palavras inglesas next (próximo) e tel (telefone). O protótipo atual apenas reproduz a interação de pressionar para falar usando Wi-Fi local.

## Atualização deste guia

A fonte deste manual é `docs/guia_do_usuario.md`. Depois de editar o texto, execute `python docs/gerar_pdf.py` para recriar `output/pdf/Nextel_Local_Guia_do_Usuario.pdf`.
