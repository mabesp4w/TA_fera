# Generated migration to remove merek field from KendaraanBermotor

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crud', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='kendaraanbermotor',
            name='kendaraan_b_jenis_i_283cd9_idx',
        ),
        migrations.RemoveField(
            model_name='kendaraanbermotor',
            name='merek',
        ),
        migrations.AddIndex(
            model_name='kendaraanbermotor',
            index=models.Index(fields=['jenis', 'type_kendaraan'], name='kendaraan_b_jenis_i_283cd9_idx'),
        ),
    ]

