from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="BehaviorEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.UUIDField()),
                ("product_id", models.UUIDField()),
                ("product_service", models.CharField(max_length=32)),
                ("event_type", models.CharField(choices=[("product_view", "Product View"), ("cart_add", "Cart Add"), ("purchase", "Purchase")], max_length=32)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UserItemAggregate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.UUIDField()),
                ("product_id", models.UUIDField()),
                ("product_service", models.CharField(max_length=32)),
                ("last_event_type", models.CharField(blank=True, default="", max_length=32)),
                ("view_count", models.PositiveIntegerField(default=0)),
                ("cart_add_count", models.PositiveIntegerField(default=0)),
                ("purchase_count", models.PositiveIntegerField(default=0)),
                ("total_quantity", models.PositiveIntegerField(default=0)),
                ("last_event_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updated_at"], "unique_together": {("user_id", "product_service", "product_id")}},
        ),
    ]
