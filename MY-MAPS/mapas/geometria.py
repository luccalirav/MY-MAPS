"""Geometria do bloqueio: janela do mapa, círculo de 150 m, quarteirões da área.

Tudo é calculado em graus (lon, lat), com as mesmas convenções do PDF modelo:
1° de latitude = 110.574 m e 1° de longitude = 111.320 m x cos(latitude).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely import affinity
from shapely.geometry import Point, box

from . import config
from .kml import MapaKML, Quarteirao


class ErroGeometria(ValueError):
    """Situação em que não dá para montar o mapa sem adivinhar."""


@dataclass
class Janela:
    lon0: float
    lat0: float
    km_lon: float            # metros por grau de longitude nesta latitude
    meia_largura: float      # graus
    meia_altura: float       # graus
    ppd_lat: float           # pontos (pt) por grau de latitude
    ppd_lon: float
    view: object             # caixa (polígono) da janela

    def pt_por_metro_lat(self) -> float:
        return self.ppd_lat / config.M_POR_GRAU_LAT


@dataclass
class ItemArea:
    quarteirao: Quarteirao
    localidade: str          # nome com iniciais maiúsculas; vazio se fora de qualquer localidade
    eh_notificacao: bool


@dataclass
class Resultado:
    lat: float
    lon: float
    janela: Janela
    circulo: object
    itens: list[ItemArea] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def notificacao(self) -> ItemArea:
        return next(i for i in self.itens if i.eh_notificacao)


def criar_janela(lat: float, lon: float, largura_pt: float, altura_pt: float) -> Janela:
    cosl = math.cos(math.radians(lat))
    km_lon = config.M_POR_GRAU_LON_EQUADOR * cosl
    hh = config.MARGEM_M / config.M_POR_GRAU_LAT
    ppd_lat = altura_pt / (2 * hh)
    ppd_lon = ppd_lat * cosl                                   # aspecto 1/cos(lat)
    hw = largura_pt / (2 * ppd_lon)
    return Janela(lon, lat, km_lon, hw, hh, ppd_lat, ppd_lon, box(lon - hw, lat - hh, lon + hw, lat + hh))


def criar_circulo(lat: float, lon: float):
    """Elipse em graus: é exatamente o que aparece desenhado no papel."""
    cosl = math.cos(math.radians(lat))
    km_lon = config.M_POR_GRAU_LON_EQUADOR * cosl
    return affinity.scale(Point(lon, lat).buffer(1, 128),
                          xfact=config.RAIO_M / km_lon, yfact=config.RAIO_M / config.M_POR_GRAU_LAT,
                          origin=(lon, lat))


def _localidade_de(geom, mapa: MapaKML) -> str:
    """Localidade com maior área de sobreposição com o quarteirão."""
    melhor, melhor_area = '', 0.0
    for loc in mapa.localidades:
        area = geom.intersection(loc.geom).area
        if area > melhor_area:
            melhor, melhor_area = loc.nome, area
    return melhor.title()


def analisar(mapa: MapaKML, lat: float, lon: float, janela: Janela) -> Resultado:
    ponto = Point(lon, lat)
    circulo = criar_circulo(lat, lon)

    itens = [ItemArea(q, _localidade_de(q.geom, mapa), q.geom.contains(ponto))
             for q in mapa.quarteiroes if q.geom.intersects(circulo)]

    centros = [i for i in itens if i.eh_notificacao]
    if not centros:
        proximo = min(mapa.quarteiroes, key=lambda q: q.geom.distance(ponto), default=None)
        dica = ''
        if proximo is not None:
            metros = proximo.geom.distance(ponto) * config.M_POR_GRAU_LAT
            dist = f'{metros:.1f}' if metros < 10 else f'{metros:.0f}'
            dica = f' (mais próximo: QRT {proximo.numero} {proximo.referencia}, a ~{dist} m)'.replace('  ', ' ')
        raise ErroGeometria('o ponto não está dentro de nenhum quarteirão do KML' + dica)
    if len(centros) > 1:
        raise ErroGeometria('o ponto cai em mais de um quarteirão (sobreposição no KML): '
                            + ', '.join(f'QRT {c.quarteirao.numero}' for c in centros))

    itens.sort(key=lambda i: (int(i.quarteirao.numero) if i.quarteirao.numero else 9999, i.localidade))

    avisos = []
    for i in itens:
        q = i.quarteirao
        rotulo = f'QRT {q.numero}' if q.numero else f'quarteirão "{q.nome}"'
        if not q.numero:
            avisos.append(f'{rotulo} está sem número no KML')
        if not q.referencia:
            avisos.append(f'{rotulo} sem referência')
        if not i.localidade:
            avisos.append(f'{rotulo} fora de qualquer localidade')
    for q in mapa.outros:
        if q.geom.intersects(janela.view):
            avisos.append(f'polígono da camada Notificações dentro da janela: {q.nome} {q.referencia}'.strip())
    return Resultado(lat, lon, janela, circulo, itens, avisos)


def ponto_do_rotulo(geom, janela: Janela):
    """Centroide se estiver na janela; senão, um ponto dentro da parte visível."""
    c = geom.centroid
    if janela.view.contains(c):
        return c
    visivel = geom.intersection(janela.view)
    return None if visivel.is_empty else visivel.representative_point()
