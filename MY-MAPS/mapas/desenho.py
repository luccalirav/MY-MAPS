"""Montagem do PDF de bloqueio, idêntico ao modelo "R. Ver. Antônio Rebelatto, 16".

Medidas em pt, a partir do canto superior esquerdo da página A4 paisagem.
Veja prompt_base_mapa_bloqueio.md para o passo a passo e as justificativas.
"""
from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, Patch, Rectangle
from matplotlib.patches import Polygon as MPoly

from . import config, geometria
from .geometria import Resultado
from .kml import MapaKML

PAGINA_W, PAGINA_H = 841.68, 595.44
MAPA = dict(x0=27.0350113881, x1=562.1409886, top=59.5, bot=494.2)
LEGENDA = dict(x0=674.2, x1=824.8, top=59.5, bot=494.2)
MAPA_LARGURA = MAPA['x1'] - MAPA['x0']
MAPA_ALTURA = MAPA['bot'] - MAPA['top']

AMARELO, VERMELHO, VERMELHO_ESC = '#FFEA00', '#FF5252', '#D50000'
K_BASE = 0.572            # linha de base = topo do texto + K_BASE x tamanho da fonte


def _partes(g):
    return list(g.geoms) if hasattr(g, 'geoms') else [g]


def _anel(poly, lon0, lat0):
    return [(x - lon0, y - lat0) for x, y in poly.exterior.coords]


def gerar_pdf(mapa: MapaKML, endereco: str, lat: float, lon: float, saida: str | Path) -> Resultado:
    """Gera o PDF em `saida` e devolve o resultado da análise (quarteirões, avisos...)."""
    janela = geometria.criar_janela(lat, lon, MAPA_LARGURA, MAPA_ALTURA)
    res = geometria.analisar(mapa, lat, lon, janela)
    fig = None
    try:
        fig = _desenhar(mapa, res, endereco)
        fig.savefig(str(saida), format='pdf')
    finally:
        if fig is not None:
            plt.close(fig)
    return res


def _desenhar(mapa: MapaKML, res: Resultado, endereco: str):
    lat, lon, jan, view = res.lat, res.lon, res.janela, res.janela.view
    area_ids = {id(i.quarteirao) for i in res.itens}
    locs_vis = [l for l in mapa.localidades if l.geom.intersects(view)]
    cx_mapa = (MAPA['x0'] + MAPA['x1']) / 2
    cy_mapa = (MAPA['top'] + MAPA['bot']) / 2

    fig = plt.figure(figsize=(PAGINA_W / 72, PAGINA_H / 72), dpi=72)
    ov = fig.add_axes([0, 0, 1, 1], zorder=10)
    ov.set_xlim(0, PAGINA_W); ov.set_ylim(PAGINA_H, 0); ov.axis('off'); ov.patch.set_alpha(0)
    ax = fig.add_axes([MAPA['x0'] / PAGINA_W, (PAGINA_H - MAPA['bot']) / PAGINA_H,
                       MAPA_LARGURA / PAGINA_W, MAPA_ALTURA / PAGINA_H], zorder=1)
    ax.set_xlim(-jan.meia_largura, jan.meia_largura); ax.set_ylim(-jan.meia_altura, jan.meia_altura)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_linewidth(0.8)

    # ------------------------------------------------------------ mapa (de baixo para cima)
    # 1) quarteirões fora da área
    for q in mapa.quarteiroes:
        if id(q) in area_ids or not q.geom.intersects(view):
            continue
        for p in _partes(q.geom):
            if p.geom_type == 'Polygon':
                ax.add_patch(MPoly(_anel(p, lon, lat), closed=True, fc='white', ec='0.6', lw=0.5, zorder=2))
    # 2) quarteirões da área
    for it in res.itens:
        for p in _partes(it.quarteirao.geom):
            if p.geom_type != 'Polygon':
                continue
            ax.add_patch(MPoly(_anel(p, lon, lat), closed=True,
                               fc=VERMELHO if it.eh_notificacao else AMARELO, ec='black',
                               lw=1.4 if it.eh_notificacao else 0.8, zorder=3))
    # 3) localidades por cima dos quarteirões (transparência 0,13) e bordas tracejadas
    for l in mapa.localidades:
        for p in _partes(l.geom):
            if p.geom_type == 'Polygon' and p.intersects(view):
                ax.add_patch(MPoly(_anel(p, lon, lat), closed=True, fc=l.cor, ec='none', alpha=0.13,
                                   lw=0, zorder=4))
    for l in locs_vis:
        for p in _partes(l.geom):
            if p.geom_type == 'Polygon':
                ax.add_patch(MPoly(_anel(p, lon, lat), closed=True, fill=False, ec=l.cor, lw=2.2,
                                   ls='--', zorder=5))
    # 4) círculo de 150 m
    ax.add_patch(Ellipse((0, 0), 2 * config.RAIO_M / jan.km_lon, 2 * config.RAIO_M / config.M_POR_GRAU_LAT,
                         fill=False, ec=VERMELHO_ESC, lw=2.2, zorder=6))
    # 5) números dos quarteirões fora da área
    for q in mapa.quarteiroes:
        if id(q) in area_ids or not q.numero or not q.geom.intersects(view):
            continue
        c = geometria.ponto_do_rotulo(q.geom, jan)
        if c is not None:
            ax.text(c.x - lon, c.y - lat, q.numero, ha='center', va='center', fontsize=7,
                    color='0.5333', zorder=7, clip_on=True)
    # 6) nomes das localidades
    for l in locs_vis:
        visivel = l.geom.intersection(view)
        if visivel.is_empty:
            continue
        rp = visivel.representative_point()
        ax.text(rp.x - lon, rp.y - lat, l.nome.upper(), ha='center', va='center', fontsize=11,
                fontweight='bold', color='0.2', alpha=0.35, zorder=7, clip_on=True)
    # 7) números da área, em caixa branca translúcida
    for it in res.itens:
        c = geometria.ponto_do_rotulo(it.quarteirao.geom, jan)
        if c is None:
            continue
        ax.text(c.x - lon, c.y - lat, it.quarteirao.numero or 'S/N', ha='center', va='center',
                fontsize=11, fontweight='bold', color='black', zorder=8, clip_on=True,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.75))

    # ------------------------------------------------------------ escala, norte e pin
    def T(x, topo, texto, tamanho, negrito=False, cor='black', ha='left', **kw):
        return ov.text(x, topo + K_BASE * tamanho, texto, ha=ha, va='baseline', fontsize=tamanho,
                       fontweight='bold' if negrito else 'normal', color=cor, **kw)

    esc_x0, esc_y = 48.4, 476.8
    esc_len = 50 * jan.ppd_lat / config.M_POR_GRAU_LON_EQUADOR
    ov.plot([esc_x0, esc_x0 + esc_len], [esc_y, esc_y], color='black', lw=3.0, solid_capstyle='butt', zorder=20)
    T(esc_x0 + esc_len / 2, 466.0, '50 m', 8, ha='center', zorder=20)

    nx = 535.39                      # seta do norte: cabeça com o azul padrão do matplotlib, como no modelo
    ov.plot([nx, nx], [97.9, 91.11], color='black', lw=2.0, solid_capstyle='round', zorder=20)
    ov.add_patch(MPoly([(nx - 2.8, 91.11), (nx, 85.51), (nx + 2.8, 91.11)], closed=True, fc='#1f77b4',
                       ec='black', lw=2.0, joinstyle='round', zorder=21))
    T(535.36, 103.5, 'N', 14, True, ha='center', zorder=20)

    ponta_x, ponta_y = cx_mapa, cy_mapa           # pin: ponta no ponto da notificação (10 x 17 pt)
    h, r = 12.0, 5.0
    beta = math.acos(r / h)
    cc_x, cc_y = ponta_x, ponta_y - h
    t0 = math.pi / 2 - beta
    arco = np.linspace(t0, t0 - (2 * math.pi - 2 * beta), 80)
    verts = [(ponta_x, ponta_y)] + [(cc_x + r * math.cos(t), cc_y + r * math.sin(t)) for t in arco] \
        + [(ponta_x, ponta_y)]
    ov.add_patch(MPoly(verts, closed=True, fc=VERMELHO_ESC, ec='black', lw=1.0, joinstyle='round', zorder=30))
    ov.add_patch(Circle((cc_x, cc_y), 3.4, fc='white', ec='none', zorder=31))

    # ------------------------------------------------------------ cabeçalho
    T(PAGINA_W / 2, 18.6, 'BLOQUEIO DE NOTIFICAÇÃO – RAIO DE 150 m (300 m de diâmetro)', 14, True, ha='center')
    T(PAGINA_W / 2, 39.3, 'Município de Porecatu – PR  |  Vigilância Ambiental', 10, ha='center')

    # ------------------------------------------------------------ legenda lateral
    rend = fig.canvas.get_renderer()

    def largura(texto, tamanho, negrito=False):
        t = ov.text(0, 0, texto, fontsize=tamanho, fontweight='bold' if negrito else 'normal')
        w = t.get_window_extent(rend).width
        t.remove()
        return w

    ov.add_patch(Rectangle((LEGENDA['x0'], LEGENDA['top']), LEGENDA['x1'] - LEGENDA['x0'],
                           LEGENDA['bot'] - LEGENDA['top'], fc='white', ec='black', lw=1.2, zorder=1))
    T(681.4, 67.1, 'Quarteirões na área', 10, True)
    larg_max = LEGENDA['x1'] - 697.3 - 5

    def quebrar(texto, tamanho):
        linhas, atual = [], ''
        for palavra in texto.split():
            teste = (atual + ' ' + palavra).strip()
            if largura(teste, tamanho) <= larg_max or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas or ['']

    linhas_leg = [(it, quebrar(it.quarteirao.referencia, 7.5) if it.quarteirao.referencia else [])
                  for it in res.itens]
    passo, extra = 21.96, 9.3
    precisa = sum(passo + extra * max(0, len(ls) - 1) for _, ls in linhas_leg)
    disponivel = LEGENDA['bot'] - 6 - 88.3
    if precisa > disponivel:                       # muitos quarteirões: comprime o passo
        k = disponivel / precisa
        passo *= k
        extra *= k
    y = 88.3
    for it, ls in linhas_leg:
        q = it.quarteirao
        ov.add_patch(Rectangle((681.4, y), 9.4, 9.4, fc=VERMELHO if it.eh_notificacao else AMARELO,
                               ec='black', lw=0.6, zorder=3))
        T(697.3, y + 0.6, q.numero or 'S/N', 9.5, True)
        if it.localidade:
            T(718.5, y + 1.3, '– ' + it.localidade, 6.8, cor='0.4')
        for i, ln in enumerate(ls):
            T(697.3, y + 11.8 + 9.3 * i, ln, 7.5)
        y += passo + extra * max(0, len(ls) - 1)

    # ------------------------------------------------------------ rodapé: quadro de dados
    texto_coord = f'{lat:.6f}, {lon:.6f}'
    url = f'https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}'
    larg_end = largura(endereco, 8.5, True)
    q_x1 = 260.9
    linhas_end = [endereco]
    if 97.3 + larg_end > q_x1 - 5:
        q_x1 = min(276.0, 97.3 + larg_end + 8)
        if 97.3 + larg_end > q_x1 - 5:             # ainda não cabe: quebra a linha
            linhas_end = textwrap.wrap(endereco, 30)
            q_x1 = 260.9
    ov.add_patch(Rectangle((25.3, 504.8), q_x1 - 25.3, 588.3 - 504.8, fc='white', ec='black', lw=1.2, zorder=1))
    T(32.5, 513.9, 'ENDEREÇO:', 8.5, True)
    yy = 513.9
    for ln in linhas_end:
        T(97.3, yy, ln, 8.5, True)
        yy += 10.8
    T(97.3, yy, texto_coord, 8.5, True, cor='#1155CC', url=url)
    ov.plot([97.3, 97.3 + largura(texto_coord, 8.5, True)], [yy + 8.6, yy + 8.6], color='#1155CC', lw=0.8,
            zorder=5, url=url)
    yy += 19.7
    T(32.5, yy, 'DATA DA NOTIFICAÇÃO:  __/__/____', 8.5, True)
    yy += 9.4
    T(32.5, yy, 'DATA DA ATIVIDADE:  __/__/____', 8.5, True)
    yy += 11.9
    T(32.5, yy, 'RESPONSÁVEL: Idalma', 8.5, True)

    # ------------------------------------------------------------ rodapé: legendas
    base = (PAGINA_H - 584.3) / PAGINA_H
    h1 = [Patch(fc=VERMELHO, ec='black', lw=1.0), Patch(fc=AMARELO, ec='black', lw=1.0),
          Patch(fc='none', ec=VERMELHO_ESC, lw=1.0)]
    l1 = fig.legend(h1, ['Quarteirão da notificação', 'Dentro da área', 'Raio de 150 m'],
                    title='Notificação', loc='lower left', bbox_to_anchor=(286.0 / PAGINA_W, base),
                    borderaxespad=0, fontsize=8, title_fontsize=8.5, fancybox=False,
                    edgecolor='black', framealpha=1)
    l1.get_frame().set_linewidth(1.0)
    h2 = [Patch(fc=l.cor, ec=l.cor, alpha=0.45, lw=1.0) for l in locs_vis]
    l2 = fig.legend(h2, [l.nome.title() for l in locs_vis], title='Localidade', ncol=2, columnspacing=1.5,
                    loc='lower left', bbox_to_anchor=(445.9 / PAGINA_W, base), borderaxespad=0,
                    fontsize=8, title_fontsize=8.5, fancybox=False, edgecolor='black', framealpha=1)
    l2.get_frame().set_linewidth(1.0)
    return fig
