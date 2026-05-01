from django.db import models


class EmbeddingProfile(models.Model):
    """Embedding 配置模板，管理员可创建不同量化级别的配置"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)                                    # 配置名称，如"轻量级"
    embedding_model = models.CharField(max_length=200)                        # huggingface 模型名
    quantization = models.CharField(max_length=20, blank=True, default="")   # "4bit"/"8bit"/"" 定量
    chunk_size = models.IntegerField(default=800)
    chunk_overlap = models.IntegerField(default=120)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'embedding_profile'
        managed = True
        verbose_name = 'Embedding 配置'
        verbose_name_plural = 'Embedding 配置列表'

    def __str__(self):
        q_str = f" ({self.quantization})" if self.quantization else ""
        return f"{self.name}{q_str}"


class KnowledgeBase(models.Model):
    STATUS_CHOICES = [
        ("pending_review", "???"),
        ("active", "???"),
        ("rejected", "???"),
        ("archived", "???"),
    ]
    KIND_CHOICES = [
        ("knowledge_base", "???"),
        ("dataset", "???"),
        ("document", "??"),
    ]

    id = models.BigAutoField(primary_key=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="document", db_index=True)
    parent_knowledge_base = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='child_documents'
    )
    content = models.TextField(blank=True, default="")
    metadata = models.JSONField(blank=True, null=True)
    collection_name = models.CharField(max_length=200, blank=True, default="")
    embedding_profile = models.ForeignKey(
        EmbeddingProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="knowledge_bases"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    version = models.IntegerField(default=1)
    supersedes = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_base'
        managed = True
        verbose_name = '?????'
        verbose_name_plural = '???????'
        ordering = ["-updated_at"]

    def __str__(self):
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get("name", f"KB {self.id}")
        return f"KB {self.id}"

class TravelScraperSight(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    introduce = models.TextField()
    score = models.CharField(max_length=20)
    position = models.CharField(max_length=255)
    grade = models.CharField(max_length=100)
    images = models.TextField() # longtext
    comments = models.TextField() # longtext
    url = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    city_id = models.BigIntegerField()

    class Meta:
        managed = False # This table already exists in MySQL
        db_table = 'travel_scraper_sight'


class AdminQATestSession(models.Model):
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("passed", "已通过"),
        ("failed", "未通过"),
    ]

    id = models.BigAutoField(primary_key=True)
    admin_user_id = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=200, default="新建测试")
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="qa_test_sessions",
    )
    provider_id = models.CharField(max_length=100, blank=True, default="")
    provider_name = models.CharField(max_length=200, blank=True, default="")
    model_name = models.CharField(max_length=200, blank=True, default="")
    mode = models.CharField(max_length=20, blank=True, default="normal")
    use_web_search = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    release_enabled = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    latest_question = models.TextField(blank=True, default="")
    latest_answer = models.TextField(blank=True, default="")
    latest_latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_qa_test_session'
        managed = True
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return self.title or f"QA Session {self.id}"


class AdminQATestMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "用户"),
        ("assistant", "助手"),
    ]

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        AdminQATestSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(blank=True, default=list)
    citations = models.JSONField(blank=True, default=list)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_qa_test_message'
        managed = True
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:32]}"

class FinalCompleteDataset(models.Model):
    # This table has no primary key, Django requires one.
    # We will treat 'name' or a composite as ID, or use row_number if possible, 
    # but for simple read-only access we can try to use 'name' if unique, or add a managed=False warning.
    # Given the schema, let's assume we can read it but might have issues with specific row selection if no unique ID.
    # We'll map fields based on inspect output.
    
    name = models.CharField(max_length=255, primary_key=True) # Assuming name is unique enough for display
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    star_rating = models.CharField(max_length=255)
    score = models.CharField(max_length=255)
    price = models.CharField(max_length=255)
    sales_volume = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    is_free = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    longitude = models.CharField(max_length=255)
    latitude = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    keywords = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'final_complete_dataset'


class TravelItineraryItem(models.Model):
    user_id = models.CharField(max_length=64, db_index=True)
    spot_key = models.CharField(max_length=120)
    spot_name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True, default="")
    price = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    cover_image = models.TextField(blank=True, default="")
    recommendation_reason = models.CharField(max_length=255, blank=True, default="")
    tags = models.JSONField(blank=True, default=list)
    spot_snapshot = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "travel_itinerary_item"
        managed = True
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user_id", "spot_key"], name="unique_itinerary_spot_per_user"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.spot_name}"


class TravelBookingIntent(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("contacted", "Contacted"),
        ("archived", "Archived"),
    ]

    user_id = models.CharField(max_length=64, db_index=True)
    trip_name = models.CharField(max_length=200, blank=True, default="")
    contact_name = models.CharField(max_length=100, blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_estimated_cost = models.FloatField(default=0)
    items = models.JSONField(blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "travel_booking_intent"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.trip_name or f"Booking Intent {self.id}"


class TravelDiscoverySignal(models.Model):
    SIGNAL_CHOICES = [
        ("view", "View"),
        ("itinerary_add", "Itinerary Add"),
        ("booking_intent", "Booking Intent"),
    ]

    user_id = models.CharField(max_length=64, db_index=True)
    spot_key = models.CharField(max_length=120, db_index=True)
    signal_type = models.CharField(max_length=30, choices=SIGNAL_CHOICES)
    payload = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "travel_discovery_signal"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user_id}:{self.signal_type}:{self.spot_key}"
