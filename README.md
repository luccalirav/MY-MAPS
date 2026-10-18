# MY-MAPS

Gera o PDF de **bloqueio de notificação** (raio de 150 m) a partir do KML do Google My Maps,
no mesmo modelo do PDF "R. Ver. Antônio Rebelatto, 16". Um PDF por endereço.

## Instalação (uma vez)

No PowerShell, dentro da pasta do projeto:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Nas próximas vezes, só ativar o ambiente: `.\.venv\Scripts\Activate.ps1`

## Uso

**1. Registrar o KML** (sempre que o mapa mudar; guarda a data da atualização e um backup do anterior):

```
python main.py kml "C:\caminho\MAPA_DE_BLOQUEIO.kml"
```

**2. Ver qual KML está em uso e quando foi atualizado:**

```
python main.py status
```

**3. Gerar mapas** (pergunta o endereço e as coordenadas, mostra o resumo e só gera depois do `s`):

```
python main.py
```

Os PDFs saem em `saida\` com o nome do endereço. Para outra pasta: `python main.py --saida "D:\PDFs"`.
Coordenadas aceitas: `-22.750384, -51.378630` (padrão do Google Maps).

## Avisos que o programa mostra
- `QRT NN sem referência` / `sem número`: dado vazio no KML. Fica em branco no mapa, nada é inventado.
- `o ponto não está dentro de nenhum quarteirão`: as coordenadas caíram na rua ou fora do KML. O PDF não é gerado.
- `polígono da camada Notificações dentro da janela`: há polígono na camada errada do KML.

## Testes

```
python -m pytest
```

## Organização

```
main.py            comandos (gerar, kml, status)
mapas/kml.py       leitura do KML e registro da data de atualização
mapas/geometria.py janela do mapa, círculo de 150 m, quarteirões da área, localidades
mapas/desenho.py   montagem do PDF idêntica ao modelo
mapas/entrada.py   perguntas e confirmação no terminal
tests/             testes automáticos (usam um KML de mentira gerado na hora)
dados/             KML atual e registro (fora do Git)
saida/             PDFs gerados (fora do Git)
```

`*.kml` e `*.pdf` estão no `.gitignore`: endereços e referências reais ficam só no PC.
