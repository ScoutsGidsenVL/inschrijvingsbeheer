from django.db import migrations, models

import inschrijfbeheer.models.inschrijfbeheer_models


class Migration(migrations.Migration):
    """Deelnemer.id volgt lid.id uit de Groepsadministratie: varchar(255).

    Django past de foreign key inschrijving.lid mee aan.
    """

    dependencies = [
        ("inschrijfbeheer", "0002_sequences"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deelnemer",
            name="id",
            field=models.CharField(
                default=inschrijfbeheer.models.inschrijfbeheer_models.volgende_deelnemer_id,
                max_length=255,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
