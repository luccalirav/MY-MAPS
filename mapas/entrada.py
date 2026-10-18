"""Conversa no terminal: pede endereço e coordenadas, mostra o resumo e só gera após confirmação."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

SAIR = {'sair', 'exit', 'quit'}
SIM = {'s', 'sim', 'y', 'yes'}
NAO = {'n', 'nao', 'não', 'no'}


def interpretar_coordenadas(texto: str) -> tuple[float, float]:
    """Aceita '-22.750384, -51.378630' (padrão do Google Maps) ou '-22,750384; -51,378630'."""
    t = (texto or '').strip().strip('()[]')
    if not t:
        raise ValueError('coordenadas vazias')
    if ';' in t:
        partes = [p.strip().replace(',', '.') for p in t.split(';')]
        if len(partes) != 2:
            raise ValueError('use apenas duas coordenadas: latitude; longitude')
        numeros = partes
    else:
        numeros = re.findall(r'-?\d+(?:\.\d+)?', t)
        if len(numeros) != 2:
            raise ValueError('não entendi. Use ponto como decimal, ex.: -22.750384, -51.378630 '
                             '(ou separe por ; se usar vírgula decimal)')
    try:
        lat, lon = float(numeros[0]), float(numeros[1])
    except ValueError:
        raise ValueError('as coordenadas precisam ser números') from None
    if not -90 <= lat <= 90:
        raise ValueError(f'latitude fora do intervalo (-90 a 90): {lat}')
    if not -180 <= lon <= 180:
        raise ValueError(f'longitude fora do intervalo (-180 a 180): {lon}')
    return lat, lon


def nome_arquivo(endereco: str) -> str:
    """Nome do PDF: o endereço, trocando só os caracteres proibidos no Windows."""
    base = re.sub(r'[\\/:*?"<>|]', '-', endereco).strip().rstrip('.')
    return (base or 'mapa') + '.pdf'


def fluxo_interativo(gerar: Callable[[str, float, float], tuple[Path, list[str]]],
                     pasta_saida: Path, entrada: Callable[[str], str] = input,
                     saida: Callable[..., None] = print) -> None:
    """Repete: endereço -> coordenadas -> confirmação -> PDF. Enter vazio ou 'sair' encerra."""
    saida("\nDigite 'sair' (ou deixe vazio no endereço) para encerrar.\n")
    while True:
        endereco = entrada('Endereço (rua e número): ').strip()
        if not endereco or endereco.lower() in SAIR:
            saida('Encerrado.')
            return

        coordenadas = None
        while coordenadas is None:
            bruto = entrada('Coordenadas (latitude, longitude): ').strip()
            if bruto.lower() in SAIR:
                saida('Encerrado.')
                return
            try:
                coordenadas = interpretar_coordenadas(bruto)
            except ValueError as e:
                saida(f'  ✗ {e}')
        lat, lon = coordenadas

        destino = Path(pasta_saida) / nome_arquivo(endereco)
        saida('\nConfira antes de gerar:')
        saida(f'  Endereço    : {endereco}')
        saida(f'  Coordenadas : {lat:.6f}, {lon:.6f}')
        saida(f'  Arquivo     : {destino.name}' + ('  (já existe e será substituído)' if destino.exists() else ''))

        resposta = ''
        while resposta not in SIM | NAO:
            resposta = entrada('Confirmar e gerar o PDF? [s/n]: ').strip().lower()
        if resposta in NAO:
            saida('Cancelado. Nada foi gerado.\n')
            continue

        try:
            caminho, avisos = gerar(endereco, lat, lon)
        except Exception as e:                       # erro em um endereço não derruba o programa
            saida(f'  ✗ Não foi possível gerar: {e}\n')
            continue
        saida(f'  ✓ PDF gerado: {caminho}')
        for aviso in avisos:
            saida(f'  ⚠ {aviso}')
        saida('')
