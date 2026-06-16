# -*- coding: utf-8 -*-
"""Compatibilidade para executar o simulador pelo nome antigo.

O modulo principal do projeto fica em `simulador.py`. Este arquivo existe
para manter funcionando o comando `python3 Simulador.py`.
"""

from simulador import *  # noqa: F401,F403


if __name__ == "__main__":
    from interface_gui import JanelaSimulador

    JanelaSimulador().executar()
