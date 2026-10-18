"""Leitura do KML (Google My Maps) e registro de quando ele foi atualizado."""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import config

NS = '{http://www.opengis.net/kml/2.2}'
CAMADA_LOCALIDADES = 'LOCALIDADES'
CAMADA_NOTIFICACOES = 'Notificações'
COR_PADRAO = '#888888'


class ErroKML(ValueError):
    """KML ausente, ilegível ou sem os dados esperados."""


@dataclass
class Quarteirao:
    numero: str          # 2 dígitos ("06"); vazio se o nome não tem número
    nome: str            # nome bruto no KML (ex.: "QRT: 6")
    referencia: str      # descrição sem o "REF:"; vazia se não houver
    geom: object         # polígono em graus (lon, lat)


@dataclass
class Localidade:
    nome: str            # como está no KML (ex.: "VILA IGUAÇU")
    cor: str             # cor da linha do polígono no KML (#rrggbb)
    geom: object


@dataclass
class MapaKML:
    quarteiroes: list[Quarteirao] = field(default_factory=list)
    localidades: list[Localidade] = field(default_factory=list)
    outros: list[Quarteirao] = field(default_factory=list)   # polígonos da camada "Notificações"


# ---------------------------------------------------------------- textos

def limpar(texto: str | None) -> str:
    return re.sub(r'\s+', ' ', (texto or '').replace('\xa0', ' ')).strip()


def numero_do_nome(nome: str) -> str:
    """Primeiro grupo de dígitos do nome, com 2 dígitos ('QRT: 6' -> '06')."""
    m = re.search(r'(\d+)', nome or '')
    return m.group(1).zfill(2) if m else ''


def referencia_da_descricao(descricao: str | None) -> str:
    return re.sub(r'^REF\s*:?\s*', '', limpar(descricao), flags=re.I)


def _cor_hex(aabbggrr: str) -> str:
    c = aabbggrr.strip()
    return '#' + c[6:8] + c[4:6] + c[2:4]


# ---------------------------------------------------------------- leitura

def carregar_kml(caminho: str | Path) -> MapaKML:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ErroKML(f'KML não encontrado: {caminho}')
    try:
        raiz = ET.parse(caminho).getroot()
    except ET.ParseError as e:
        raise ErroKML(f'Não consegui ler o KML ({e}).') from e

    estilos = {s.get('id'): s for s in raiz.iter(NS + 'Style')}
    mapas_estilo = {}
    for sm in raiz.iter(NS + 'StyleMap'):
        for par in sm.findall(NS + 'Pair'):
            if par.find(NS + 'key').text == 'normal':
                mapas_estilo[sm.get('id')] = par.find(NS + 'styleUrl').text.lstrip('#')

    def cor_da_linha(pm) -> str:
        su = pm.find(NS + 'styleUrl')
        if su is None:
            return COR_PADRAO
        sid = mapas_estilo.get(su.text.lstrip('#'), su.text.lstrip('#'))
        st = estilos.get(sid)
        ls = st.find(NS + 'LineStyle') if st is not None else None
        if ls is None or ls.find(NS + 'color') is None:
            return COR_PADRAO
        return _cor_hex(ls.find(NS + 'color').text)

    def geometria(pm):
        poligonos = []
        for pg in pm.iter(NS + 'Polygon'):
            coords = pg.find('.//' + NS + 'outerBoundaryIs//' + NS + 'coordinates').text.split()
            pts = [tuple(map(float, c.split(',')[:2])) for c in coords]
            poligonos.append(Polygon(pts).buffer(0))
        return unary_union(poligonos)

    mapa = MapaKML()
    for pasta in raiz.iter(NS + 'Folder'):
        nome_pasta = pasta.find(NS + 'name').text
        for pm in pasta.findall(NS + 'Placemark'):
            if pm.find('.//' + NS + 'Polygon') is None:
                continue
            n = pm.find(NS + 'name')
            d = pm.find(NS + 'description')
            nome = limpar(n.text if n is not None else '')
            if nome_pasta == CAMADA_LOCALIDADES:
                mapa.localidades.append(Localidade(nome, cor_da_linha(pm), geometria(pm)))
                continue
            q = Quarteirao(numero_do_nome(nome), nome,
                           referencia_da_descricao(d.text if d is not None else ''), geometria(pm))
            (mapa.outros if nome_pasta == CAMADA_NOTIFICACOES else mapa.quarteiroes).append(q)
    return mapa


# ---------------------------------------------------------------- registro de atualização

def _agora() -> datetime:
    return datetime.now().replace(microsecond=0)


def ler_info(pasta_dados: str | Path = config.PASTA_DADOS) -> dict | None:
    arq = Path(pasta_dados) / config.INFO_KML
    if not arq.is_file():
        return None
    return json.loads(arq.read_text(encoding='utf-8'))


def caminho_kml_atual(pasta_dados: str | Path = config.PASTA_DADOS) -> Path | None:
    arq = Path(pasta_dados) / config.KML_ATUAL
    return arq if arq.is_file() else None


def importar_kml(origem: str | Path, pasta_dados: str | Path = config.PASTA_DADOS,
                 agora: datetime | None = None) -> dict:
    """Valida o KML novo, guarda o anterior como backup e registra a data da atualização."""
    origem = Path(origem)
    novo = carregar_kml(origem)                                  # falha aqui se o arquivo for inválido
    if not novo.quarteiroes:
        raise ErroKML('O KML não tem nenhum quarteirão. Confira se é o arquivo certo.')

    pasta = Path(pasta_dados)
    pasta.mkdir(parents=True, exist_ok=True)
    atual = pasta / config.KML_ATUAL
    antigos = None
    if atual.is_file():
        try:
            antigos = len(carregar_kml(atual).quarteiroes)
        except ErroKML:
            antigos = None
        shutil.copy2(atual, pasta / config.KML_ANTERIOR)
    shutil.copy2(origem, atual)

    quando = (agora or _agora()).isoformat()
    info_antiga = ler_info(pasta) or {}
    historico = info_antiga.get('historico', [])
    historico.append({'data': quando, 'nome_original': origem.name,
                      'quarteiroes': len(novo.quarteiroes)})
    info = {
        'arquivo': config.KML_ATUAL,
        'nome_original': origem.name,
        'atualizado_em': quando,
        'quarteiroes': len(novo.quarteiroes),
        'localidades': len(novo.localidades),
        'quarteiroes_antes': antigos,
        'historico': historico[-50:],
    }
    (pasta / config.INFO_KML).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    return info


def formatar_data(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime('%d/%m/%Y %H:%M')
