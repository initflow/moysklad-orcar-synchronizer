# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2021-02-09 11:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import synchronizer.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalogue', '0016_auto_20190327_0757'),
        ('partner', '0005_auto_20181115_1953'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0007_auto_20181115_1953'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccumulationDiscountSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, unique=True)),
                ('active', models.BooleanField()),
                ('name', models.CharField(max_length=100, null=True)),
                ('levels', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='OrderSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_sync_id', models.CharField(max_length=100, null=True)),
                ('invoice_out_sync_id', models.CharField(max_length=100, null=True)),
                ('payment_sync_id', models.CharField(max_length=100, null=True)),
                ('status', models.CharField(max_length=100, null=True)),
                ('counter_party_id', models.CharField(max_length=100, null=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='order.Order')),
            ],
        ),
        migrations.CreateModel(
            name='ProductFolderSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, unique=True)),
                ('parent_sync_id', models.CharField(max_length=100, null=True)),
                ('path_name', models.CharField(max_length=200)),
                ('archived', models.BooleanField()),
                ('updated', models.DateTimeField()),
                ('name', models.CharField(max_length=100)),
                ('path_name_changed', models.CharField(max_length=200, null=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sync', to='catalogue.Category')),
                ('parent_product_folder_sync', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='synchronizer.ProductFolderSync')),
            ],
        ),
        migrations.CreateModel(
            name='ProductSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=10000, unique=True)),
                ('folder_sync_id', models.CharField(max_length=10000)),
                ('article', models.CharField(max_length=10000, null=True)),
                ('description', models.CharField(max_length=10000, null=True)),
                ('path_name', models.CharField(max_length=10000, null=True)),
                ('archived', models.BooleanField()),
                ('updated', models.DateTimeField()),
                ('name', models.CharField(max_length=10000, null=True)),
                ('attributes', models.CharField(default='{}', max_length=10000)),
                ('image_url', models.CharField(max_length=10000, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogue.Product')),
            ],
        ),
        migrations.CreateModel(
            name='StatesSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=100, null=True)),
                ('state_type', models.CharField(max_length=100, null=True)),
                ('entity_name', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StockByStoreSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_or_variant_sync_id', models.CharField(max_length=100, null=True)),
                ('type_enum', models.CharField(choices=[(synchronizer.models.StockTypeEnum('product'), 'product'), (synchronizer.models.StockTypeEnum('variant'), 'variant')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='StoreSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, null=True)),
                ('updated', models.DateTimeField()),
                ('name', models.CharField(max_length=100, null=True)),
                ('archived', models.BooleanField()),
                ('path_name', models.CharField(max_length=100, null=True)),
                ('address', models.CharField(max_length=150, null=True)),
                ('description', models.CharField(max_length=100, null=True)),
                ('partner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='partner.Partner')),
            ],
        ),
        migrations.CreateModel(
            name='SyncTaskObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('last_run_date', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, unique=True)),
                ('archived', models.BooleanField(default=False)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('email', models.CharField(max_length=100, null=True)),
                ('personal_discount', models.IntegerField(default=0)),
                ('demand_sum_correction', models.IntegerField(default=0)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VariantCharacteristics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
                ('variant_sync_id', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VariantSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.CharField(max_length=400, unique=True)),
                ('updated', models.DateTimeField()),
                ('name', models.CharField(max_length=400)),
                ('archived', models.BooleanField()),
                ('product_sync_id', models.CharField(max_length=400, null=True)),
                ('characteristics', models.CharField(default='{}', max_length=1000)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogue.Product')),
            ],
        ),
        migrations.AddField(
            model_name='variantcharacteristics',
            name='variant_sync_obj',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='synchronizer.VariantSync'),
        ),
        migrations.AddField(
            model_name='stockbystoresync',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='synchronizer.StoreSync'),
        ),
    ]
