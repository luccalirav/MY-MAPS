import pytest

from mapas import desenho, geometria, kml
from tests.conftest import ponto


def test_gera_pdf(kml_mini, tmp_path):
    mapa = kml.carregar_kml(kml_mini)
    lat, lon = ponto(140, 110)
    saida = tmp_path / 'teste.pdf'
    res = desenho.gerar_pdf(mapa, 'Rua Teste, 123', lat, lon, saida)
    assert saida.read_bytes().startswith(b'%PDF')
    assert saida.stat().st_size > 5_000
    assert res.notificacao.quarteirao.numero == '06'


def test_endereco_longo_nao_quebra(kml_mini, tmp_path):
    mapa = kml.carregar_kml(kml_mini)
    lat, lon = ponto(140, 110)
    desenho.gerar_pdf(mapa, 'Avenida Doutor Francisco de Assis Bezerra de Menezes Filho, 12345 - Apto 7',
                      lat, lon, tmp_path / 'longo.pdf')
    assert (tmp_path / 'longo.pdf').exists()


def test_ponto_fora_de_quarteirao_nao_gera_arquivo(kml_mini, tmp_path):
    mapa = kml.carregar_kml(kml_mini)
    lat, lon = ponto(90, 10)
    with pytest.raises(geometria.ErroGeometria):
        desenho.gerar_pdf(mapa, 'Rua Teste', lat, lon, tmp_path / 'nao.pdf')
    assert not (tmp_path / 'nao.pdf').exists()
