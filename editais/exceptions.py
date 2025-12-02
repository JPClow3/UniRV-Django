"""
Exceções customizadas para o aplicativo Editais.
"""


class EditalNotFoundError(Exception):
    """Exceção levantada quando um edital não é encontrado."""
    
    def __init__(self, identifier, message=None):
        self.identifier = identifier
        if message is None:
            message = f"Edital não encontrado: {identifier}"
        super().__init__(message)


