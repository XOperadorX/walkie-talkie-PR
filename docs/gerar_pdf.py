"""Build a three-page user guide PDF using only Python's standard library."""
from pathlib import Path
import textwrap

DEST = Path(__file__).with_name('guia_do_usuario.pdf')
W, H = 595, 842

def hextext(s):
    return s.encode('cp1252', errors='replace').hex().upper().encode('ascii')

def page(items, number):
    ops = [b'q', b'0.93 0.96 0.98 rg', b'0 0 595 842 re f', b'Q']
    for item in items:
        kind = item[0]
        if kind == 'box':
            _, x, y, w, h, color = item
            ops += [f'{color} rg'.encode(), f'{x} {y} {w} {h} re f'.encode()]
        elif kind == 'text':
            _, x, y, size, color, font, value = item
            ops += [f'BT /{font} {size} Tf {color} rg 1 0 0 1 {x} {y} Tm <'.encode() + hextext(value) + b'> Tj ET']
    ops += [b'0.38 0.49 0.59 RG 0.5 w 52 42 m 543 42 l S', b'BT /F1 8 Tf 0.38 0.49 0.59 rg 1 0 0 1 52 27 Tm <57616C6B69652D54616C6B6965204C6F63616C207C204775696120646F20757375E172696F> Tj ET']
    ops += [f'BT /F1 8 Tf 0.38 0.49 0.59 rg 1 0 0 1 535 27 Tm <{number:02d}> Tj ET'.encode()]
    return b'\n'.join(ops)

def add_text(items, value, y, size=10.5, color='0.14 0.24 0.33', bold=False, width=86, leading=None):
    leading = leading or int(size * 1.45)
    for line in textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False) or ['']:
        items.append(('text', 56, y, size, color, 'F2' if bold else 'F1', line))
        y -= leading
    return y

def heading(items, value, y):
    y -= 8
    items.append(('text', 54, y, 16, '0.03 0.49 0.54', 'F2', value))
    return y - 22

def numbered(items, values, y):
    for i, value in enumerate(values, 1):
        lines = textwrap.wrap(value, width=78, break_long_words=False, break_on_hyphens=False)
        items.append(('text', 57, y, 10, '0.03 0.49 0.54', 'F2', f'{i}.'))
        for line in lines:
            items.append(('text', 77, y, 10, '0.14 0.24 0.33', 'F1', line))
            y -= 14
        y -= 3
    return y

pages = []
p = [('box', 0, 600, W, 242, '0.06 0.16 0.26'),
     ('text', 54, 755, 12, '0.54 0.84 0.83', 'F2', 'GUIA DO USUÁRIO'),
     ('text', 54, 704, 30, '1 1 1', 'F2', 'Walkie-Talkie Local')]
add_text(p, 'Instale, conecte e converse pela rede Wi-Fi de casa ou do trabalho.', 673, 12, '0.87 0.92 0.96', width=72, leading=18)
p.append(('box', 54, 497, 487, 72, '0.87 0.96 0.95'))
add_text(p, 'COMO FUNCIONA', 547, 10, '0.03 0.49 0.54', bold=True)
add_text(p, 'O computador hospeda o servidor. Os celulares usam o mesmo roteador Wi-Fi e recebem a voz enviada para a sala geral. Não precisa de internet externa.', 527, 10, width=91)
y = heading(p, 'Antes de começar', 470)
y = add_text(p, 'Você precisa de um computador com Python 3.10 ou mais recente, um celular Android 8.0 ou mais recente e uma rede Wi-Fi privada.', y)
y = heading(p, '1. Ligar o servidor', y)
y = numbered(p, ['Abra a pasta do projeto no computador.', 'Abra o PowerShell dentro dessa pasta.', 'Digite python servidor/servidor_walkie.py e pressione Enter.', 'Se o Firewall perguntar, permita o Python em redes privadas.', 'Anote o endereço e o IP mostrados no terminal. Exemplo: http://192.168.0.10:8080.', 'Deixe a janela do PowerShell aberta durante o uso.'], y)
p.append(('box', 54, max(75, y-4), 487, 39, '0.99 0.95 0.84'))
add_text(p, 'A página usa a porta 8080. O áudio usa a porta 5000.', max(96, y+12), 9.5, '0.38 0.31 0.13', width=86)
pages.append(page(p, 1))

p = []
y = heading(p, '2. Criar seu acesso', 784)
y = numbered(p, ['No navegador, abra o endereço mostrado no terminal.', 'Informe seu nome e crie uma senha com pelo menos 8 caracteres.', 'Pressione Cadastrar.', 'Anote o ID exibido. O aplicativo pedirá esse ID e a senha.'], y)
y = heading(p, '3. Gerar e instalar o aplicativo', y)
y = add_text(p, 'O código do aplicativo está no projeto. O Android Studio gera o APK para instalar no celular.', y)
y = numbered(p, ['Instale e abra o Android Studio no computador.', 'Abra nele a pasta android que fica dentro do projeto.', 'Espere a sincronização terminar.', 'No menu, selecione Build > Build Bundle(s) / APK(s) > Build APK(s).', 'Quando terminar, localize android/app/build/outputs/apk/debug/app-debug.apk.', 'Na página do servidor, toque em Baixar APK, ou transfira o arquivo ao celular.', 'Abra o APK. Se o Android solicitar, permita instalar aplicativos desta fonte e confirme Instalar.', 'Abra o aplicativo e permita o uso do microfone.'], y)
p.append(('box', 54, max(74, y-2), 487, 42, '0.87 0.96 0.95'))
add_text(p, 'O botão Baixar APK fica disponível depois que o APK for gerado no caminho indicado.', max(99, y+14), 9.5, width=88)
pages.append(page(p, 2))

p = []
y = heading(p, '4. Conectar e conversar', 784)
y = numbered(p, ['Confirme que o servidor continua aberto no computador.', 'No app, digite o IP do computador, apenas os números. Exemplo: 192.168.0.10. Não escreva http:// nem a porta 8080.', 'Digite seu ID e sua senha e toque em Conectar.', 'Mantenha Segure para falar pressionado enquanto fala.', 'Solte o botão para terminar. Os outros usuários conectados recebem a voz.', 'Toque em Desconectar quando terminar.'], y)
y = heading(p, 'Se não conectar', y)
for label, msg in [('Mesmo Wi-Fi', 'Confira se todos estão na mesma rede. Redes de convidados podem bloquear a comunicação entre aparelhos.'), ('IP', 'Use o IP atual do terminal. Ele pode mudar após reiniciar o roteador.'), ('Firewall', 'Permita o Python em redes privadas. A página usa TCP 8080 e o áudio TCP 5000.'), ('Microfone', 'Nas configurações do Android, abra Aplicativos, Walkie-Talkie Local, Permissões e habilite Microfone.'), ('APK', 'Se a pagina disser que o APK não existe, gere-o no Android Studio conforme a seção 3.')]:
    p.append(('text', 55, y, 10, '0.03 0.49 0.54', 'F2', label + ':'))
    y = add_text(p, msg, y-14, 9.2, width=92, leading=12) - 2
y = heading(p, 'Cuidados', y)
y = add_text(p, 'Use apenas em uma rede confiável. O áudio nao tem criptografia de transporte; não encaminhe as portas do roteador para a internet. As senhas são guardadas como hashes no arquivo usuarios.json. Esta versão tem uma sala geral.', y, 9.2, width=94, leading=12)
pages.append(page(p, 3))

objects = []
def obj(data):
    objects.append(data)
    return len(objects)
catalog = obj(b'')
tree = obj(b'')
f1 = obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
f2 = obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
page_ids = []
for stream in pages:
    sid = obj(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')
    page_ids.append(obj(f'<< /Type /Page /Parent {tree} 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R >> >> /Contents {sid} 0 R >>'.encode()))
objects[catalog-1] = f'<< /Type /Catalog /Pages {tree} 0 R >>'.encode()
objects[tree-1] = f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] /Count {len(page_ids)} >>".encode()
pdf = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
offsets = [0]
for i, data in enumerate(objects, 1):
    offsets.append(len(pdf))
    pdf.extend(f'{i} 0 obj\n'.encode() + data + b'\nendobj\n')
xref = len(pdf)
pdf.extend(f'xref\n0 {len(offsets)}\n'.encode() + b'0000000000 65535 f \n')
for offset in offsets[1:]:
    pdf.extend(f'{offset:010d} 00000 n \n'.encode())
pdf.extend(f'trailer\n<< /Size {len(offsets)} /Root {catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
DEST.write_bytes(pdf)
print(f'Gerado: {DEST.resolve()} ({len(pdf)} bytes, {len(pages)} paginas)')
