class PaymentError(Exception):
    pass


class PaymentValidationError(PaymentError):
    pass


class PaymentGatewayError(PaymentError):
    pass
