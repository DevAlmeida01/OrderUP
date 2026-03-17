"""
Serviço de envio de emails do OrderUP.
Emails são enviados de forma assíncrona via thread para não travar a requisição.
"""
import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _send_async(subject, message, recipient_list, html_message=None):
    """Envia email em background para não bloquear a request."""
    def run():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"[EmailService] Erro ao enviar email: {e}")

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()


class EmailService:

    @classmethod
    def order_confirmed(cls, order):
        """Email para o cliente quando pedido é criado."""
        if not order.customer.email:
            return

        items_text = "\n".join(
            f"  • {item.quantity}x {item.menu_item.name} — R$ {item.menu_item.price:.2f}"
            for item in order.items.all()
        )

        subject = f"✅ Pedido #{order.id} confirmado — {order.restaurant.name}"
        message = f"""
Olá, {order.customer.first_name or order.customer.username}!

Seu pedido foi recebido com sucesso! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━
📋 RESUMO DO PEDIDO #{order.id}
━━━━━━━━━━━━━━━━━━━━━━━━
Restaurante: {order.restaurant.name}
Tipo: {order.get_order_type_display()}

Itens:
{items_text}

Total: R$ {order.total:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━

{'📍 Endereço de entrega: ' + order.delivery_address + ', ' + (order.delivery_neighborhood or '') if order.delivery_address else ''}

Acompanhe o status do seu pedido em: {settings.SITE_URL}/orders/{order.id}/

Obrigado por escolher o OrderUP! 🍽

— Equipe OrderUP
        """.strip()

        _send_async(subject, message, [order.customer.email])

    @classmethod
    def order_status_changed(cls, order, old_status):
        """Email para o cliente quando o status do pedido muda."""
        if not order.customer.email:
            return

        status_messages = {
            'PAID':      ('💳 Pagamento confirmado!', 'Seu pagamento foi aprovado. O restaurante já recebeu seu pedido.'),
            'PREPARING': ('👨‍🍳 Pedido em preparo!', 'O restaurante começou a preparar seu pedido. Em breve estará pronto!'),
            'READY':     ('✅ Pedido pronto!', 'Seu pedido está pronto! Em breve chegará até você.'),
            'DELIVERED': ('🎉 Pedido entregue!', 'Pedido entregue com sucesso. Bom apetite! Avalie o restaurante.'),
            'CANCELLED': ('❌ Pedido cancelado', 'Infelizmente seu pedido foi cancelado. Entre em contato com o restaurante para mais informações.'),
        }

        if order.status not in status_messages:
            return

        emoji_title, body = status_messages[order.status]
        subject = f"{emoji_title} Pedido #{order.id} — {order.restaurant.name}"
        message = f"""
Olá, {order.customer.first_name or order.customer.username}!

{body}

Pedido #{order.id} — {order.restaurant.name}
Status atual: {order.get_status_display()}
Total: R$ {order.total:.2f}

Ver detalhes: {settings.SITE_URL}/orders/{order.id}/

— Equipe OrderUP
        """.strip()

        _send_async(subject, message, [order.customer.email])

    @classmethod
    def new_order_to_restaurant(cls, order):
        """Email para o dono do restaurante quando novo pedido chega."""
        owner_email = order.restaurant.owner.email
        if not owner_email:
            return

        items_text = "\n".join(
            f"  • {item.quantity}x {item.menu_item.name}"
            for item in order.items.all()
        )

        subject = f"🔔 Novo pedido #{order.id} — {order.customer.username}"
        message = f"""
Novo pedido recebido!

Cliente: {order.customer.username}
Tipo: {order.get_order_type_display()}
Total: R$ {order.total:.2f}

Itens:
{items_text}

{'Endereço: ' + order.delivery_address if order.delivery_address else ''}

Gerenciar: {settings.SITE_URL}/orders/{order.id}/

— OrderUP
        """.strip()

        _send_async(subject, message, [owner_email])
