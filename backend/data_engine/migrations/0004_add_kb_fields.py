# Generated manually to add missing KnowledgeBase fields

import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("data_engine", "0003_embeddingprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgebase",
            name="collection_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="embedding_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_bases",
                to="data_engine.embeddingprofile",
            ),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_review", "待审核"),
                    ("active", "已激活"),
                    ("rejected", "已拒绝"),
                    ("archived", "已归档"),
                ],
                default="active",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="supersedes",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="version",
            field=models.IntegerField(default=1),
        ),
    ]