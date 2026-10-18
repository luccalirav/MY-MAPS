from datetime import datetime

import pytest

from mapas import config, kml


def test_carrega_camadas(kml_mini):
    mapa = kml.carregar_kml(kml_mini)
    assert len(mapa.quarteiroes) == 12
    assert [l.nome for l in mapa.localidades] == ['ALFA', 'BETA']
    assert len(mapa.outros) == 1


def test_numero_com_dois_digitos_e_referencia_limpa(kml_mini):
    mapa = kml.carregar_kml(kml_mini)
    q6 = next(q for q in mapa.quarteiroes if q.nome == 'QRT: 6')
    assert q6.numero == '06'
    assert q6.referencia == 'CASA 6'            # sem "REF:" e sem espaços estranhos
    q2 = next(q for q in mapa.quarteiroes if q.numero == '02')
    assert q2.referencia == ''                  # vazio continua vazio (nada é inventado)


def test_cor_da_localidade_vem_do_kml(kml_mini):
    mapa = kml.carregar_kml(kml_mini)
    assert mapa.localidades[0].cor == '#0288d1'
    assert mapa.localidades[1].cor == '#eda29b'


def test_numero_do_nome():
    assert kml.numero_do_nome('QRT: 6') == '06'
    assert kml.numero_do_nome('QRT 7') == '07'
    assert kml.numero_do_nome('QRT: 09 - TB') == '09'
    assert kml.numero_do_nome('QRT:') == ''


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(kml.ErroKML):
        kml.carregar_kml(tmp_path / 'nao_existe.kml')


def test_importar_registra_data_e_historico(kml_mini, tmp_path):
    dados = tmp_path / 'dados'
    info = kml.importar_kml(kml_mini, dados, agora=datetime(2026, 10, 18, 9, 30))
    assert (dados / config.KML_ATUAL).is_file()
    assert info['quarteiroes'] == 12 and info['quarteiroes_antes'] is None
    assert kml.formatar_data(info['atualizado_em']) == '18/10/2026 09:30'

    info2 = kml.importar_kml(kml_mini, dados, agora=datetime(2026, 10, 19, 8, 0))
    assert (dados / config.KML_ANTERIOR).is_file()           # backup do anterior
    assert info2['quarteiroes_antes'] == 12
    assert len(info2['historico']) == 2
    assert kml.ler_info(dados)['atualizado_em'].startswith('2026-10-19')


def test_importar_rejeita_kml_sem_quarteirao(tmp_path):
    vazio = tmp_path / 'vazio.kml'
    vazio.write_text('<kml xmlns="http://www.opengis.net/kml/2.2"><Document/></kml>', encoding='utf-8')
    with pytest.raises(kml.ErroKML):
        kml.importar_kml(vazio, tmp_path / 'dados')
    assert not (tmp_path / 'dados' / config.KML_ATUAL).exists()
