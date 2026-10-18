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

**Base de dados (KML):** o programa lê sozinho o **arquivo mais recente** da pasta de KML
(padrão: `C:\Users\Admin\Documents\Projetos\MY-MAPS\KML`). Para atualizar a base:
coloque o KML novo na pasta e apague o mais antigo. Não há comando de importação.
Se ficar mais de um arquivo, o programa usa o mais recente e avisa quais podem ser apagados.
Aceita `.kml` e `.kmz`. Para usar outra pasta: `python main.py --pasta-kml "D:\kml"`
ou crie `config_local.json` na raiz do projeto com `{"pasta_kml": "D:\\kml"}`.

**Gerar mapas** (pergunta o endereço e as coordenadas, mostra o resumo e só gera depois do `s`):

```
python main.py
```

Antes de confirmar, o resumo mostra também qual KML será usado e a data do arquivo.
Os PDFs saem em `saida\` com o nome do endereço. Para outra pasta: `python main.py --saida "D:\PDFs"`.
Coordenadas aceitas: `-22.750384, -51.378630` (padrão do Google Maps).

**Ver qual KML está em uso:** `python main.py status`

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
mapas/kml.py       leitura do KML e escolha do arquivo mais recente da pasta
mapas/geometria.py janela do mapa, círculo de 150 m, quarteirões da área, localidades
mapas/desenho.py   montagem do PDF idêntica ao modelo
mapas/entrada.py   perguntas e confirmação no terminal
tests/             testes automáticos (usam um KML de mentira gerado na hora)
saida/             PDFs gerados (fora do Git)
```

`*.kml`, `*.kmz`, `*.pdf` e a pasta `KML/` estão no `.gitignore`: endereços e referências reais ficam só no PC.
