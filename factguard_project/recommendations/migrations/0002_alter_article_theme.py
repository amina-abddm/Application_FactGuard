from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ('recommendations', '0001_initial'),

    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="theme",
            field=models.CharField(
                choices=[
                    ("politics", "Politique"),
                    ("finance", "Finance"),
                    ("sports", "Sport"),
                    ("technology", "Technologie"),
                    ("science", "Science"),
                    ("culture", "Culture"),
                    ("world", "International"),

            model_name='article',
            name='theme',
            field=models.CharField(choices=[('politics', 'Politique'), ('finance', 'Finance'), ('sports', 'Sport'), ('technology', 'Technologie'), ('science', 'Science'), ('culture', 'Culture'), ('world', 'International'), ('health', 'Santé')], max_length=20),

        ),
    ]
