from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("data_engine", "0004_add_kb_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminQATestSession",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("admin_user_id", models.CharField(db_index=True, max_length=64)),
                ("title", models.CharField(default="新建测试", max_length=200)),
                ("provider_id", models.CharField(blank=True, default="", max_length=100)),
                ("provider_name", models.CharField(blank=True, default="", max_length=200)),
                ("model_name", models.CharField(blank=True, default="", max_length=200)),
                ("mode", models.CharField(blank=True, default="normal", max_length=20)),
                ("use_web_search", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "草稿"), ("passed", "已通过"), ("failed", "未通过")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("release_enabled", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True, default="")),
                ("latest_question", models.TextField(blank=True, default="")),
                ("latest_answer", models.TextField(blank=True, default="")),
                ("latest_latency_ms", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "knowledge_base",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="qa_test_sessions",
                        to="data_engine.knowledgebase",
                    ),
                ),
            ],
            options={
                "db_table": "admin_qa_test_session",
                "ordering": ["-updated_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="AdminQATestMessage",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("user", "用户"), ("assistant", "助手")], max_length=20)),
                ("content", models.TextField()),
                ("sources", models.JSONField(blank=True, default=list)),
                ("citations", models.JSONField(blank=True, default=list)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="data_engine.adminqatestsession",
                    ),
                ),
            ],
            options={
                "db_table": "admin_qa_test_message",
                "ordering": ["created_at", "id"],
            },
        ),
    ]
