import os
import shutil
import time
import zipfile

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


def _copiar(origem, pasta, nome, deslocamento_s):
    """Copia o KML para a pasta com data de modificação 'agora + deslocamento' (no futuro, p/ vencer o ctime)."""
    pasta.mkdir(exist_ok=True)
    destino = pasta / nome
    shutil.copy(origem, destino)
    t = time.time() + deslocamento_s
    os.utime(destino, (t, t))
    return destino


def test_usa_o_kml_mais_recente_da_pasta(kml_mini, tmp_path):
    pasta = tmp_path / 'KML'
    _copiar(kml_mini, pasta, 'MAPA (4).kml', 1000)
    _copiar(kml_mini, pasta, 'MAPA (5).kml', 2000)
    fonte = kml.FonteKML(pasta)
    assert fonte.arquivo().nome == 'MAPA (5).kml'
    assert len(fonte.avisos()) == 1 and 'MAPA (4).kml' in fonte.avisos()[0]     # sugere apagar o antigo


def test_apagando_o_antigo_nao_ha_aviso(kml_mini, tmp_path):
    pasta = tmp_path / 'KML'
    _copiar(kml_mini, pasta, 'MAPA (5).kml', 2000)
    assert kml.FonteKML(pasta).avisos() == []


def test_recarrega_quando_chega_um_kml_novo(kml_mini, tmp_path):
    pasta = tmp_path / 'KML'
    _copiar(kml_mini, pasta, 'MAPA (4).kml', 1000)
    fonte = kml.FonteKML(pasta)
    mapa1, arq1 = fonte.carregar()
    assert fonte.carregar()[0] is mapa1                       # sem mudança: usa o cache
    _copiar(kml_mini, pasta, 'MAPA (5).kml', 2000)
    mapa2, arq2 = fonte.carregar()
    assert arq2.nome == 'MAPA (5).kml' and mapa2 is not mapa1


def test_ignora_temporarios_e_outros_formatos(kml_mini, tmp_path):
    pasta = tmp_path / 'KML'
    _copiar(kml_mini, pasta, 'MAPA.kml', 1000)
    _copiar(kml_mini, pasta, '~$MAPA.kml', 5000)
    (pasta / 'anotacoes.txt').write_text('oi')
    assert [a.nome for a in kml.listar_kmls(pasta)] == ['MAPA.kml']


def test_pasta_inexistente_ou_vazia(tmp_path):
    with pytest.raises(kml.ErroKML, match='não encontrada'):
        kml.listar_kmls(tmp_path / 'nao_existe')
    (tmp_path / 'vazia').mkdir()
    with pytest.raises(kml.ErroKML, match='nenhum arquivo'):
        kml.listar_kmls(tmp_path / 'vazia')


def test_le_kmz(kml_mini, tmp_path):
    kmz = tmp_path / 'mapa.kmz'
    with zipfile.ZipFile(kmz, 'w') as z:
        z.write(kml_mini, 'doc.kml')
    assert len(kml.carregar_kml(kmz).quarteiroes) == 12


def test_pasta_kml_prioridade(tmp_path, monkeypatch):
    assert config.pasta_kml('X:\\outra') == __import__('pathlib').Path('X:\\outra')
    local = tmp_path / 'config_local.json'
    local.write_text('{"pasta_kml": "D:\\\\meus\\\\kml"}', encoding='utf-8')
    monkeypatch.setattr(config, 'ARQUIVO_LOCAL', local)
    assert str(config.pasta_kml()) == 'D:\\meus\\kml'
    monkeypatch.setattr(config, 'ARQUIVO_LOCAL', tmp_path / 'nao_existe.json')
    assert config.pasta_kml() == config.PASTA_KML_PADRAO
