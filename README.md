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

## Atualizar a base (KML)

Não existe comando de atualização. O programa lê sozinho o **KML mais recente** que estiver na pasta:

```
C:\Users\Admin\Documents\Projetos\MY-MAPS\KML
```

Para atualizar a base:

1. Exporte o KML do Google My Maps.
2. Coloque o arquivo novo na pasta `KML`.
3. Apague o arquivo mais antigo.

Pronto: o próximo PDF já usa o KML novo, sem reiniciar o programa.

- **Qual arquivo vale:** o de data mais recente (no Windows, vale a mais nova entre a data de modificação e a de criação do arquivo).
- **Mais de um arquivo na pasta:** o programa usa o mais recente e avisa quais podem ser apagados. Apagar o antigo é só para evitar confusão.
- **Como conferir:** o programa mostra o nome e a data do arquivo em uso ao abrir e no resumo antes de gerar cada PDF.
  Se aparecer o arquivo errado, responda `n` e arrume a pasta.
- **Formatos:** `.kml` e `.kmz` (arquivos temporários e ocultos são ignorados).
- **Pasta vazia ou inexistente:** o programa avisa e não gera nada.
- **Outra pasta:** `python main.py --pasta-kml "D:\kml"`, ou crie `config_local.json` na raiz do projeto com
  `{"pasta_kml": "D:\\kml"}`. A pasta padrão fica em `mapas/config.py`.

## Gerar mapas

```
python main.py
```

O programa pergunta o **endereço** (rua e número) e as **coordenadas**, um de cada vez, mostra o resumo
(endereço, coordenadas, nome do PDF e KML em uso) e só gera depois do `s`. Com `n`, nada é gerado.
Para encerrar, deixe o endereço vazio ou digite `sair`.

- Coordenadas aceitas: `-22.750384, -51.378630` (padrão do Google Maps).
- Os PDFs saem em `saida\` com o nome do endereço. Outra pasta: `python main.py --saida "D:\PDFs"`.
  Se já existir um PDF com o mesmo nome, o resumo avisa que ele será substituído.

**Ver qual KML está em uso, sem gerar nada:** `python main.py status`

## Avisos que o programa mostra

- `QRT NN sem referência` / `sem número`: dado vazio no KML. Fica em branco no mapa, nada é inventado.
- `o ponto não está dentro de nenhum quarteirão`: as coordenadas caíram na rua ou fora do KML. O PDF não é gerado.
- `polígono da camada Notificações dentro da janela`: há polígono na camada errada do KML.
- `há N arquivos na pasta do KML`: sobrou KML antigo na pasta; pode apagar.
- `Pasta do KML não encontrada` / `Não há nenhum arquivo .kml`: confira a pasta `KML`.

## Testes

```
python -m pytest
```

## Organização

```
main.py             comandos (gerar mapas e status)
mapas/config.py     constantes e pasta do KML
mapas/kml.py        leitura do KML e escolha do arquivo mais recente da pasta
mapas/geometria.py  janela do mapa, círculo de 150 m, quarteirões da área, localidades
mapas/desenho.py    montagem do PDF idêntica ao modelo
mapas/entrada.py    perguntas e confirmação no terminal
tests/              testes automáticos (usam um KML de mentira gerado na hora)
docs/               prompt-base com o passo a passo de montagem do PDF
saida/              PDFs gerados (fora do Git)
```

`*.kml`, `*.kmz`, `*.pdf`, a pasta `KML/` e o `config_local.json` estão no `.gitignore`:
endereços e referências reais ficam só no PC.