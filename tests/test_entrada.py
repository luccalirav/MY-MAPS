from pathlib import Path

import pytest

from mapas import entrada


@pytest.mark.parametrize('texto, esperado', [
    ('-22.750384, -51.378630', (-22.750384, -51.37863)),
    ('-22.756150416742027, -51.37377703497339', (-22.756150416742027, -51.37377703497339)),
    ('(-22.75 -51.37)', (-22.75, -51.37)),
    ('-22,750384; -51,378630', (-22.750384, -51.37863)),
])
def test_coordenadas_validas(texto, esperado):
    assert entrada.interpretar_coordenadas(texto) == esperado


@pytest.mark.parametrize('texto', ['', 'abc', '-22.75', '-22,75 -51,37', '95.0, -51.3', '-22.7, -190.0'])
def test_coordenadas_invalidas(texto):
    with pytest.raises(ValueError):
        entrada.interpretar_coordenadas(texto)


def test_nome_arquivo():
    assert entrada.nome_arquivo('R. Geraldo Lopes da Silva, 2480') == 'R. Geraldo Lopes da Silva, 2480.pdf'
    assert entrada.nome_arquivo('Rua A/B: 10?') == 'Rua A-B- 10-.pdf'


def _rodar(respostas, tmp_path):
    fila = iter(respostas)
    chamadas, mensagens = [], []

    def gerar(endereco, lat, lon):
        chamadas.append((endereco, lat, lon))
        return tmp_path / 'x.pdf', ['QRT 02 sem referência']

    entrada.fluxo_interativo(gerar, tmp_path, entrada=lambda _: next(fila), saida=mensagens.append)
    return chamadas, '\n'.join(map(str, mensagens))


def test_confirmando_gera_o_pdf(tmp_path):
    chamadas, texto = _rodar(['Rua X, 10', '-22.75, -51.37', 's', ''], tmp_path)
    assert chamadas == [('Rua X, 10', -22.75, -51.37)]
    assert 'Rua X, 10' in texto and '-22.750000, -51.370000' in texto      # devolve o que foi informado
    assert 'sem referência' in texto


def test_cancelando_nao_gera_nada(tmp_path):
    chamadas, texto = _rodar(['Rua X, 10', '-22.75, -51.37', 'n', ''], tmp_path)
    assert chamadas == []
    assert 'Nada foi gerado' in texto


def test_coordenada_errada_pergunta_de_novo(tmp_path):
    chamadas, texto = _rodar(['Rua X, 10', 'lixo', '-22.75, -51.37', 's', 'sair'], tmp_path)
    assert len(chamadas) == 1 and '✗' in texto


def test_erro_ao_gerar_nao_derruba_o_programa(tmp_path):
    fila = iter(['Rua X, 10', '-22.75, -51.37', 's', ''])
    msgs = []

    def gerar(*a):
        raise RuntimeError('deu ruim')

    entrada.fluxo_interativo(gerar, tmp_path, entrada=lambda _: next(fila), saida=msgs.append)
    assert any('deu ruim' in str(m) for m in msgs)
