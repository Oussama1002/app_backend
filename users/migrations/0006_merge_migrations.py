from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_region_route'),
        ('users', '0005_internaluser_parameters_alter_customuser_options_and_more'),
    ]

    operations = [
        # Integrate changes from 0003_region_route
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('region_code', models.ForeignKey('Region', on_delete=models.CASCADE)),
            ],
        ),

        # Integrate changes from 0005_internaluser_parameters_alter_customuser_options_and_more
        migrations.CreateModel(
            name='InternalUser',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('username', models.CharField(max_length=100)),
                ('email', models.EmailField(unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=100, unique=True),
        ),
        # Additional operations to reconcile differences...
    ]
