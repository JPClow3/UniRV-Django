"""
Exceções customizadas para o aplicativo Editais.

Este módulo define exceções específicas do domínio para melhor
tratamento de erros e logging.
"""


class EditalException(Exception):
    """Exceção base para erros relacionados a editais."""
    pass


class EditalNotFoundError(EditalException):
    """Exceção levantada quando um edital não é encontrado."""
    
    def __init__(self, identifier, message=None):
        self.identifier = identifier
        if message is None:
            message = f"Edital não encontrado: {identifier}"
        super().__init__(message)


