class EZIDError(Exception):

    """base class for EZID errors"""

class MintError(EZIDError):

    """error minting DOI"""

    def __init__(self, message):
        self.message = message
        return

    def __str__(self):
        return self.message

class UpdateError(EZIDError):

    """error minting DOI"""

    def __init__(self, message):
        self.message = message
        return

    def __str__(self):
        return self.message

class RequestError(EZIDError):

    """EZID error"""

    def __init__(self, message):
        self.message = message
        return

    def __str__(self):
        return self.message

class NotCreatedError(EZIDError):

    """DOI not yet created"""

class ExistsError(EZIDError):

    """DOI already exists"""

class NotFoundError(EZIDError):

    """DOI does not exist"""

    def __init__(self, identifier):
        self.identifier = identifier
        return

    def __str__(self):
        return 'DOI %s not found' % self.identifier

# eof
