"""Configuração comum: marcador de rastreabilidade ``req``."""


def pytest_configure(config):
    config.addinivalue_line("markers", "req(id): requisito da documentação rastreado pelo teste")
    config.addinivalue_line("markers", "alvo(trecho): trecho de código não coberto que o teste estrutural mira")
