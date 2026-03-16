from django.db import models


class DisasterReport(models.Model):
    DISASTER_CHOICES = [
        ('Fire', 'Fire'),
        ('Flood', 'Flood'),
        ('Accident', 'Accident'),
        ('Earthquake', 'Earthquake'),
        ('Cyclone', 'Cyclone'),
        ('Landslide', 'Landslide'),
        ('Tsunami', 'Tsunami'),
        ('Chemical Spill', 'Chemical Spill'),
        ('Other', 'Other'),
    ]

    CROWD_LEVEL_CHOICES = [
        ('Minimal',  'Minimal'),
        ('Low',      'Low'),
        ('Moderate', 'Moderate'),
        ('High',     'High'),
        ('Critical', 'Critical'),
        ('Unknown',  'Unknown'),
    ]

    disaster_type    = models.CharField(max_length=50, choices=DISASTER_CHOICES, db_index=True)
    location         = models.CharField(max_length=200)
    latitude         = models.FloatField(null=True, blank=True)
    longitude        = models.FloatField(null=True, blank=True)
    estimated_people = models.IntegerField(default=0)
    crowd_level      = models.CharField(max_length=10, choices=CROWD_LEVEL_CHOICES, default='Unknown')
    description      = models.TextField()
    reported_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.disaster_type} at {self.location}"

    @property
    def crowd_level_emoji(self):
        return {'Minimal':'🔵','Low':'🟢','Moderate':'🟡','High':'🔴','Critical':'🚨'}.get(self.crowd_level,'⚪')

class DisasterPhoto(models.Model):
    PHOTO_TYPE_CHOICES = [
        ('before', 'Before'),
        ('during', 'During'),
        ('after',  'After'),
    ]
    disaster    = models.ForeignKey(DisasterReport, on_delete=models.CASCADE, related_name='photos')
    photo       = models.ImageField(upload_to='disaster_photos/')
    caption     = models.CharField(max_length=200, blank=True)
    photo_type  = models.CharField(max_length=10, choices=PHOTO_TYPE_CHOICES, default='during')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['photo_type', 'uploaded_at']

    def __str__(self):
        return f"Photo for {self.disaster} ({self.photo_type})"

class DisasterUpdate(models.Model):
    disaster    = models.ForeignKey(DisasterReport, on_delete=models.CASCADE, related_name='updates')
    author_name = models.CharField(max_length=100, default='Anonymous')
    content     = models.TextField()
    upvotes     = models.IntegerField(default=0)
    reported_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-upvotes', '-reported_at']

    def __str__(self):
        return f"Update by {self.author_name} on {self.disaster}"


class UpdateUpvote(models.Model):
    """Tracks which IPs have upvoted which updates (prevents duplicate upvotes)."""
    update     = models.ForeignKey(DisasterUpdate, on_delete=models.CASCADE, related_name='upvote_records')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('update', 'ip_address')

    def __str__(self):
        return f"{self.ip_address} upvoted update #{self.update.pk}"


class MissingPerson(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Found', 'Found'),
        ('Deceased', 'Deceased'),
    ]

    name               = models.CharField(max_length=100)
    age                = models.IntegerField()
    gender             = models.CharField(max_length=20, choices=GENDER_CHOICES)
    last_seen_location = models.CharField(max_length=200)
    body_marks         = models.TextField(help_text="Scars, tattoos, clothing, etc.", blank=True)
    photo              = models.ImageField(upload_to='missing_photos/', null=True, blank=True)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', db_index=True)
    status_changed_at  = models.DateTimeField(null=True, blank=True)
    status_note        = models.TextField(blank=True, help_text="Optional note when status is updated")
    reported_at        = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


class InjuredPerson(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    SEVERITY_CHOICES = [
        ('Minor', 'Minor'),
        ('Moderate', 'Moderate'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Recovering', 'Recovering'),
        ('Discharged', 'Discharged'),
    ]

    name              = models.CharField(max_length=100)
    age               = models.IntegerField()
    gender            = models.CharField(max_length=20, choices=GENDER_CHOICES)
    injury_type       = models.CharField(max_length=200)
    severity          = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True)
    location          = models.CharField(max_length=200)
    description       = models.TextField(blank=True)
    photo             = models.ImageField(upload_to='injured_photos/', null=True, blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', db_index=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    status_note       = models.TextField(blank=True, help_text="Optional note when status is updated")
    reported_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.name} - {self.severity} ({self.status})"


class Donation(models.Model):
    PAYMENT_CHOICES = [
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Net Banking', 'Net Banking'),
        ('Cash', 'Cash'),
    ]

    name         = models.CharField(max_length=100)
    email        = models.EmailField()
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    purpose      = models.CharField(max_length=100)
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_CHOICES)
    donated_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        return f"{self.name} - ₹{self.amount} ({self.payment_mode})"


class CrowdData(models.Model):
    """Stores crowd snapshots at a location over time."""
    location     = models.CharField(max_length=200)
    latitude     = models.FloatField(null=True, blank=True)
    longitude    = models.FloatField(null=True, blank=True)
    people_count = models.IntegerField()
    level        = models.CharField(max_length=10)
    recorded_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.location} - {self.people_count} people ({self.level})"

class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('inaccurate', 'Inaccurate Information'),
        ('spam',       'Spam / Duplicate'),
        ('outdated',   'Outdated Report'),
        ('other',      'Other'),
    ]
    CONTENT_TYPE_CHOICES = [
        ('disaster', 'Disaster Report'),
        ('missing',  'Missing Person'),
        ('injured',  'Injured Person'),
        ('general',  'General Feedback'),
    ]

    feedback_type  = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='other')
    content_type   = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='general')
    object_id      = models.PositiveIntegerField(null=True, blank=True)   # pk of flagged object
    reporter_name  = models.CharField(max_length=100, blank=True, default='Anonymous')
    reporter_email = models.EmailField(blank=True)
    message        = models.TextField()
    resolved       = models.BooleanField(default=False, db_index=True)
    submitted_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.feedback_type} on {self.content_type} #{self.object_id or '–'}"