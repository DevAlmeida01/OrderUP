"""
Serviço de pagamento via MercadoPago.
Documentação: https://www.mercadopago.com.br/developers/pt/docs
"""
import mercadopago
from django.conf import settings
from django.urls import reverse


class PaymentService:

    @classmethod
    def _sdk(cls):
        return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    @classmethod
    def create_preference(cls, order, request) -> dict:
        """
        Cria uma preferência de pagamento no MercadoPago.
        Retorna {'init_point': url_checkout, 'preference_id': id}
        """
        sdk = cls._sdk()
        site_url = settings.SITE_URL

        items = []
        for item in order.items.all():
            items.append({
                "id": str(item.menu_item.id),
                "title": item.menu_item.name,
                "quantity": item.quantity,
                "unit_price": float(item.menu_item.price),
                "currency_id": "BRL",
            })

        preference_data = {
            "items": items,
            "payer": {
                "name": order.customer.first_name or order.customer.username,
                "email": order.customer.email or "cliente@orderup.com.br",
            },
            "back_urls": {
                "success": f"{site_url}{reverse('payment_success', args=[order.id])}",
                "failure": f"{site_url}{reverse('payment_failure', args=[order.id])}",
                "pending": f"{site_url}{reverse('payment_pending', args=[order.id])}",
            },
            "auto_return": "approved",
            "notification_url": f"{site_url}{reverse('mercadopago_webhook')}",
            "external_reference": str(order.id),
            "statement_descriptor": "ORDERUP",
            "expires": False,
        }

        response = sdk.preference().create(preference_data)
        preference = response["response"]

        # Modo sandbox usa sandbox_init_point
        if settings.DEBUG:
            init_point = preference.get("sandbox_init_point", preference.get("init_point"))
        else:
            init_point = preference.get("init_point")

        return {
            "init_point": init_point,
            "preference_id": preference.get("id"),
        }

    @classmethod
    def get_payment_info(cls, payment_id: str) -> dict:
        """Consulta informações de um pagamento pelo ID."""
        sdk = cls._sdk()
        response = sdk.payment().get(payment_id)
        return response.get("response", {})
