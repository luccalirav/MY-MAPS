"""Leitura do KML (Google My Maps) e registro de quando ele foi atualizado."""
from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import unary_union


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
        if caminho.suffix.lower() == '.kmz':          # KMZ = zip com o KML dentro (doc.kml)
            with zipfile.ZipFile(caminho) as z:
                nomes = [n for n in z.namelist() if n.lower().endswith('.kml')]
                if not nomes:
                    raise ErroKML('O KMZ não contém nenhum arquivo .kml.')
                interno = 'doc.kml' if 'doc.kml' in nomes else nomes[0]
                raiz = ET.fromstring(z.read(interno))
        else:
            raiz = ET.parse(caminho).getroot()
    except (ET.ParseError, zipfile.BadZipFile) as e:
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


# ---------------------------------------------------------------- pasta do KML

@dataclass
class ArquivoKML:
    caminho: Path
    data: datetime       # data do arquivo (a mais recente entre modificação e criação, no Windows)

    @property
    def nome(self) -> str:
        return self.caminho.name

    @property
    def data_formatada(self) -> str:
        return self.data.strftime('%d/%m/%Y %H:%M')


def _data_do_arquivo(caminho: Path) -> datetime:
    st = caminho.stat()
    ts = max(st.st_mtime, st.st_ctime) if os.name == 'nt' else st.st_mtime   # no Windows, ctime = criação
    return datetime.fromtimestamp(ts).replace(microsecond=0)


def listar_kmls(pasta: str | Path) -> list[ArquivoKML]:
    """KML/KMZ da pasta, do mais recente para o mais antigo (ignora temporários e ocultos)."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise ErroKML(f'Pasta do KML não encontrada: {pasta}\n'
                      '  Crie a pasta, ou aponte outra com --pasta-kml (ou config_local.json).')
    achados = [ArquivoKML(p, _data_do_arquivo(p)) for p in pasta.iterdir()
               if p.is_file() and p.suffix.lower() in ('.kml', '.kmz') and not p.name.startswith(('~', '.'))]
    if not achados:
        raise ErroKML(f'Não há nenhum arquivo .kml na pasta: {pasta}')
    return sorted(achados, key=lambda a: (a.data, a.nome), reverse=True)


class FonteKML:
    """Usa sempre o KML mais recente da pasta; recarrega sozinho se o arquivo mudar."""

    def __init__(self, pasta: str | Path):
        self.pasta = Path(pasta)
        self._cache = None                      # (assinatura, MapaKML)

    def arquivo(self) -> ArquivoKML:
        return listar_kmls(self.pasta)[0]

    def avisos(self) -> list[str]:
        todos = listar_kmls(self.pasta)
        if len(todos) > 1:
            antigos = ', '.join(a.nome for a in todos[1:])
            return [f'há {len(todos)} arquivos na pasta do KML; usando o mais recente. '
                    f'Pode apagar os mais antigos: {antigos}']
        return []

    def carregar(self) -> tuple[MapaKML, ArquivoKML]:
        arq = self.arquivo()
        st = arq.caminho.stat()
        assinatura = (arq.caminho, st.st_mtime_ns, st.st_size)
        if self._cache is None or self._cache[0] != assinatura:
            self._cache = (assinatura, carregar_kml(arq.caminho))
        return self._cache[1], arq
