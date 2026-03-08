from django.db import models


class BrokerToken(models.Model):
    username = models.CharField(max_length=50, unique=True)
    broker_name = models.CharField(max_length=20) # 'Zerodha' or 'Angel'
    access_token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.broker_name}"