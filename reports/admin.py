from django.contrib import admin
from .models import DisasterReport, MissingPerson, InjuredPerson, Donation, CrowdData


@admin.register(DisasterReport)
class DisasterReportAdmin(admin.ModelAdmin):
    list_display  = ('disaster_type', 'location', 'crowd_level', 'estimated_people', 'reported_at')
    list_filter   = ('disaster_type', 'crowd_level')
    search_fields = ('location', 'description')
    readonly_fields = ('reported_at',)


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display  = ('name', 'age', 'gender', 'last_seen_location', 'status', 'reported_at')
    list_filter   = ('status', 'gender')
    search_fields = ('name', 'last_seen_location')
    readonly_fields = ('reported_at', 'updated_at')


@admin.register(InjuredPerson)
class InjuredPersonAdmin(admin.ModelAdmin):
    list_display  = ('name', 'age', 'severity', 'location', 'status', 'reported_at')
    list_filter   = ('severity', 'status', 'gender')
    search_fields = ('name', 'location', 'injury_type')
    readonly_fields = ('reported_at', 'updated_at')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'amount', 'purpose', 'payment_mode', 'donated_at')
    list_filter   = ('payment_mode',)
    search_fields = ('name', 'email', 'purpose')
    readonly_fields = ('donated_at',)


@admin.register(CrowdData)
class CrowdDataAdmin(admin.ModelAdmin):
    list_display  = ('location', 'people_count', 'level', 'recorded_at')
    list_filter   = ('level',)
    search_fields = ('location',)
    readonly_fields = ('recorded_at',)