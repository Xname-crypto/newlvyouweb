# Migration to create EmbeddingProfile table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_engine", "0002_finalcompletedataset_travelscrapersight"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmbeddingProfile",
            fields=[
                ("id", models.BigAutoField(primary_key=True)),
                ("name", models.CharField(max_length=100)),
                ("embedding_model", models.CharField(max_length=200)),
                (
                    "quantization",
                    models.CharField(blank=True, default="", max_length=20),
                ),
                ("chunk_size", models.IntegerField(default=800)),
                ("chunk_overlap", models.IntegerField(default=120)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Embedding 配置",
                "verbose_name_plural": "Embedding 配置列表",
                "db_table": "embedding_profile",
            },
        ),
    ]