from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_menuitem_image'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_complement',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_neighborhood',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_cep',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[
                    ('pix', 'PIX'),
                    ('credito', 'Cartão de Crédito'),
                    ('debito', 'Cartão de Débito'),
                    ('dinheiro', 'Dinheiro'),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_notified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='last_status_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('message', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='auth.user',
                )),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='status_logs',
                    to='myapp.order',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RestaurantSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_email', models.EmailField(blank=True)),
                ('whatsapp_number', models.CharField(blank=True, max_length=20)),
                ('delivery_radius_km', models.DecimalField(decimal_places=1, default=5.0, max_digits=5)),
                ('min_order_value', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('delivery_fee', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('estimated_delivery_minutes', models.PositiveIntegerField(default=45)),
                ('accepts_delivery', models.BooleanField(default=True)),
                ('accepts_local', models.BooleanField(default=True)),
                ('restaurant', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='settings',
                    to='myapp.restaurant',
                )),
            ],
            options={
                'verbose_name': 'Configurações do Restaurante',
            },
        ),
    ]
