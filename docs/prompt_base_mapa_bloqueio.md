# Prompt-base: PDF de bloqueio de notificação (raio de 150 m)

Você vai montar, para cada notificação, um PDF idêntico ao modelo "R. Ver. Antônio Rebelatto, 16". Siga os passos na ordem. Não invente dado nenhum: se faltar número, referência ou localidade no KML, deixe em branco e avise.

## 0. Entradas
- **Endereço** (rua e número), exatamente como o usuário digitou.
- **Coordenadas** (latitude, longitude) do ponto da notificação.
- **Arquivo KML** do Google My Maps (camadas: quarteirões, `LOCALIDADES`, `Notificações`).
- O usuário confirma endereço e coordenadas antes de você montar o PDF.

## 1. Dados do KML
1. **Quarteirões:** polígonos da camada principal. Nome no formato `QRT: NN`; o número vem dos dígitos do nome e é exibido com 2 dígitos (`6` → `06`). A descrição `REF: ...` é a referência (remova o `REF:`; se vazia, fica em branco).
2. **Localidades:** polígonos da camada `LOCALIDADES`. A **cor de cada localidade** é a cor de linha do polígono no KML (não invente cores). A ordem das localidades é a ordem do KML.
3. **Camada `Notificações`:** ignorar. Se algum polígono dela entrar na janela do mapa, avisar o usuário.
4. Trabalhe em graus (longitude/latitude), sem reprojetar.

## 2. Geometria (o que contar como 150 m)
- Constantes: **1° de latitude = 110.574 m**; **1° de longitude = 111.320 m × cos(latitude da notificação)**.
- **Círculo do bloqueio:** elipse em graus com raios `150 / (111320·cos φ)` (longitude) e `150 / 110574` (latitude), centrada no ponto. No papel ele sai ~0,67% mais alto que largo; isso é esperado.
- **Janela do mapa:** centrada no ponto, **meia altura de 190 m** (latitude). A largura sai da proporção da caixa do mapa com aspecto `1/cos φ` (meia largura ≈ 235 m).
- **Quarteirão da notificação:** o que **contém** o ponto. Tem que ser exatamente um (zero ou mais de um = erro).
- **Quarteirões "dentro da área":** todos os que **tocam o círculo, mesmo parcialmente**, mais o quarteirão da notificação.
- **Localidade de cada quarteirão** (para a legenda): a localidade com **maior área de sobreposição** com ele.

## 3. Página
- A4 paisagem: **841,68 × 595,44 pt**. Fonte **DejaVu Sans**. Fundo branco.
- Todas as posições abaixo em pt, medidas a partir do canto superior esquerdo.
- Posição vertical de textos: informo o **topo** do texto; a linha de base é `topo + 0,572 × tamanho da fonte`.

## 4. Cabeçalho
- Título, **negrito 14**, centralizado em x = 420,84, topo 18,6: `BLOQUEIO DE NOTIFICAÇÃO – RAIO DE 150 m (300 m de diâmetro)`
- Subtítulo, normal 10, centralizado, topo 39,3: `Município de Porecatu – PR  |  Vigilância Ambiental` (dois espaços ao redor do `|`).

## 5. Mapa (caixa x 27,035 → 562,141; y 59,5 → 494,2; moldura preta 0,8)
Desenhe nesta ordem (de baixo para cima):
1. **Quarteirões fora da área:** preenchimento branco, contorno cinza `0.6`, espessura 0,5.
2. **Quarteirões da área:** preenchimento **#FFEA00**, contorno preto 0,8. O quarteirão da notificação: **#FF5252**, contorno preto 1,4.
3. **Localidades (por cima dos quarteirões):** cada polígono preenchido com a cor da sua localidade, **transparência 0,13**, sem contorno. Por isso quarteirões amarelos em Sidonia ficam mais esverdeados/oliva.
4. **Bordas das localidades visíveis na janela:** linha tracejada (padrão `--`, 3,7 / 1,6 × espessura), espessura 2,2, na cor da localidade, opaca.
5. **Círculo:** contorno **#D50000**, espessura 2,2, sem preenchimento.
6. **Números dos quarteirões fora da área:** cinza `0.5333`, tamanho 7, no centroide do polígono (se o centroide estiver fora da janela, no ponto representativo da parte visível).
7. **Nome das localidades visíveis:** MAIÚSCULAS, negrito 11, cor `0.2` com transparência 0,35, no ponto representativo de (localidade ∩ janela); corte na borda do mapa (nomes que passam do limite ficam cortados).
8. **Números dos quarteirões da área:** negrito 11, preto, no centroide (mesma regra do item 6), dentro de caixa arredondada branca de transparência 0,75 (`round, pad 0.15`, sem borda).
9. **Escala:** linha preta de espessura 3 a partir de x = 48,4, y = 476,8, comprimento de 50 m (≈ 56,8 pt); texto `50 m` tamanho 8, centralizado sobre a linha, topo 466,0.
10. **Norte:** haste preta (espessura 2, ponta arredondada) em x = 535,39 de y = 97,9 a 91,11; cabeça triangular (532,59;91,11) (535,39;85,51) (538,19;91,11), preenchimento **#1F77B4**, contorno preto 2; letra `N` negrito 14, centralizada em x = 535,36, topo 103,5.
11. **Pin:** ponta exatamente no centro do mapa (294,585; 276,88). Gota com círculo de raio 5,0 centrado 12,0 acima da ponta (10 × 17 pt), preenchimento **#D50000**, contorno preto 1,0; miolo branco de raio 3,4 no mesmo centro do círculo.

## 6. Legenda lateral (caixa x 674,2 → 824,8; y 59,5 → 494,2; moldura preta 1,2)
- Título `Quarteirões na área`, negrito 10, x = 681,4, topo 67,1.
- Uma linha por quarteirão da área, a partir do topo 88,3, **passo de 21,96 pt**:
  - Quadrado 9,4 × 9,4 em x = 681,4 (**vermelho #FF5252** para o quarteirão da notificação, **amarelo #FFEA00** para os demais), contorno preto 0,6.
  - Número: negrito 9,5, x = 697,3, topo da linha + 0,6.
  - `– Localidade` (primeira letra de cada palavra maiúscula): cinza `0.4`, tamanho 6,8, x = 718,5, topo da linha + 1,3.
  - Referência: tamanho 7,5, x = 697,3, topo da linha + 11,8. Se não couber na largura (até x ≈ 819,8), quebre em mais linhas de 9,3 pt e empurre as linhas seguintes. Se ainda estourar a caixa, comprima o passo.
- **Ordem:** número crescente; empate pelo nome da localidade em ordem alfabética (ex.: `10 – Metropole` antes de `10 – Sidonia`).

## 7. Rodapé
**Quadro de dados** (caixa x 25,3 → 260,9; y 504,8 → 588,3; moldura preta 1,2). Todos os textos em **negrito 8,5**:
- `ENDEREÇO:` em x = 32,5, topo 513,9; o endereço em x = 97,3 na mesma linha. Se não couber, alargue a caixa até x = 276; se ainda não couber, quebre a linha.
- Abaixo (topo 524,7), em x = 97,3: coordenadas `latitude, longitude` com **6 casas decimais**, cor **#1155CC**, sublinhadas (linha de espessura 0,8 em y = 533,3), com **link** `https://www.google.com/maps/search/?api=1&query=LAT,LON` (6 casas).
- `DATA DA NOTIFICAÇÃO:  __/__/____` (dois espaços), x = 32,5, topo 544,5. Fica em branco para preencher à mão.
- `DATA DA ATIVIDADE:  __/__/____`, x = 32,5, topo 553,9.
- `RESPONSÁVEL: Idalma`, x = 32,5, topo 565,8.

**Caixa "Notificação"** (canto inferior esquerdo em x = 286,0; base em y = 584,3; moldura preta 1,0; cantos retos; fundo branco). Título `Notificação` (8,5, normal, centralizado), itens em tamanho 8, com amostras de 16 × 5,6 pt:
1. vermelho **#FF5252** com contorno preto: `Quarteirão da notificação`
2. amarelo **#FFEA00** com contorno preto: `Dentro da área`
3. sem preenchimento, contorno **#D50000**: `Raio de 150 m`

**Caixa "Localidade"** (canto inferior esquerdo em x = 445,9; base em y = 584,3; mesmo estilo). Título `Localidade`; **2 colunas** (espaço entre colunas 1,5 × fonte); uma amostra por localidade **visível na janela**, na ordem do KML, com a cor da localidade em transparência 0,45 e contorno da mesma cor; nome com iniciais maiúsculas.

## 8. Arquivo de saída
- Um PDF por endereço, com o nome `<endereço>.pdf` (trocar apenas caracteres proibidos em nome de arquivo).

## 9. Regras de fidelidade
- Nunca preencher número, referência ou localidade que estejam vazios no KML; deixar em branco e listar o aviso (ex.: `QRT 08 sem referência`).
- Não escolher quarteirão "mais próximo" por conta própria.
- Avisar quando polígonos da camada `Notificações` entrarem na janela ou quando houver quarteirão sem número na área.
- Em caso de dúvida, perguntar antes de montar.

## 10. Conferência final
Comparar com o modelo "R. Ver. Antônio Rebelatto, 16": mesmas posições, cores, tamanhos e transparências. Diferenças aceitáveis: apenas as vindas de dados mais novos do KML (quarteirões novos, números novos).
