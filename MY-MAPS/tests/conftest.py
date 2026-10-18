"""KML de mentira para os testes: grade de 4 x 3 quarteirões em duas localidades."""
import math

import pytest

LAT0, LON0 = -22.75, -51.38
LARG, ALT, PASSO_X, PASSO_Y = 80, 60, 100, 80          # metros (rua de 20 m entre quarteirões)


def _lat(y):
    return LAT0 + y / 110574.0


def _lon(x):
    return LON0 + x / (111320.0 * math.cos(math.radians(LAT0)))


def ponto(x, y):
    """(lat, lon) de um ponto a x m a leste e y m ao norte da origem."""
    return _lat(y), _lon(x)


def _poligono(x0, y0, x1, y1):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    coords = ' '.join(f'{_lon(x)},{_lat(y)},0' for x, y in pts)
    return ('<Polygon><outerBoundaryIs><LinearRing><coordinates>'
            f'{coords}</coordinates></LinearRing></outerBoundaryIs></Polygon>')


def montar_kml():
    qrt = []
    for j in range(3):
        for i in range(4):
            n = i + j * 4 + 1
            x0, y0 = i * PASSO_X, j * PASSO_Y
            nome = 'QRT: 6' if n == 6 else f'QRT: {n:02d}'
            ref = '' if n == 2 else f'REF:\xa0 CASA {n}'
            qrt.append(f'<Placemark><name>{nome}</name><description>{ref}</description>'
                       f'{_poligono(x0, y0, x0 + LARG, y0 + ALT)}</Placemark>')
    locs = [
        ('ALFA', 'ffd18802', _poligono(-500, -500, 190, 500)),     # #0288D1
        ('BETA', 'ff9ba2ed', _poligono(190, -500, 900, 500)),      # #EDA29B
    ]
    loc_xml = ''.join(f'<Placemark><name>{n}</name><styleUrl>#{n}</styleUrl>{g}</Placemark>' for n, c, g in locs)
    estilos = ''.join(f'<Style id="{n}"><LineStyle><color>{c}</color></LineStyle></Style>' for n, c, g in locs)
    outros = ('<Placemark><name>QRT: 99</name><description>REF: FORA</description>'
              f'{_poligono(5000, 5000, 5050, 5050)}</Placemark>')
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            f'{estilos}<Folder><name>Camada sem título</name>{"".join(qrt)}</Folder>'
            f'<Folder><name>LOCALIDADES</name>{loc_xml}</Folder>'
            f'<Folder><name>Notificações</name>{outros}</Folder></Document></kml>')


@pytest.fixture
def kml_mini(tmp_path):
    arq = tmp_path / 'mini.kml'
    arq.write_text(montar_kml(), encoding='utf-8')
    return arq
