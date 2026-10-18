import pytest

from mapas import desenho, geometria, kml
from tests.conftest import ponto


@pytest.fixture
def mapa(kml_mini):
    return kml.carregar_kml(kml_mini)


def _analisar(mapa, x, y):
    lat, lon = ponto(x, y)
    jan = geometria.criar_janela(lat, lon, desenho.MAPA_LARGURA, desenho.MAPA_ALTURA)
    return geometria.analisar(mapa, lat, lon, jan)


def test_quarteirao_da_notificacao_e_area(mapa):
    res = _analisar(mapa, 140, 110)                       # centro do quarteirão 06
    assert res.notificacao.quarteirao.numero == '06'
    numeros = [i.quarteirao.numero for i in res.itens]
    assert numeros == ['01', '02', '03', '05', '06', '07', '09', '10', '11']
    assert not {'04', '08', '12'} & set(numeros)          # a 160 m: fora do raio de 150 m


def test_localidade_por_maior_sobreposicao(mapa):
    res = _analisar(mapa, 140, 110)
    por_num = {i.quarteirao.numero: i.localidade for i in res.itens}
    assert por_num['01'] == 'Alfa' and por_num['06'] == 'Alfa'
    assert por_num['03'] == 'Beta' and por_num['11'] == 'Beta'


def test_avisos_sem_inventar_dados(mapa):
    res = _analisar(mapa, 140, 110)
    assert 'QRT 02 sem referência' in res.avisos


def test_ponto_na_rua_gera_erro_com_dica(mapa):
    with pytest.raises(geometria.ErroGeometria, match='mais próximo'):
        _analisar(mapa, 90, 10)                           # rua entre os quarteirões 01 e 02


def test_circulo_tem_300_m_de_diametro_nas_unidades_do_modelo(mapa):
    import math
    lat, lon = ponto(0, 0)
    xmin, ymin, xmax, ymax = geometria.criar_circulo(lat, lon).bounds
    largura_m = (xmax - xmin) * 111320.0 * math.cos(math.radians(lat))
    altura_m = (ymax - ymin) * 110574.0
    assert largura_m == pytest.approx(300.0, abs=0.5)
    assert altura_m == pytest.approx(300.0, abs=0.5)


def test_janela_tem_meia_altura_de_190_m(mapa):
    lat, lon = ponto(0, 0)
    jan = geometria.criar_janela(lat, lon, desenho.MAPA_LARGURA, desenho.MAPA_ALTURA)
    assert jan.meia_altura * 110574.0 == pytest.approx(190.0)
    assert jan.view.contains(geometria.Point(lon, lat))
