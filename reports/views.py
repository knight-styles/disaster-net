import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Sum
from .models import (
    DisasterReport, MissingPerson, InjuredPerson, Donation,
    DisasterPhoto, DisasterUpdate, UpdateUpvote, Feedback
)
from .utils import get_crowd_for_location, crowd_level, reverse_geocode, geocode_address

def home(request):
    disasters = DisasterReport.objects.order_by('-reported_at')[:5]
    missing   = MissingPerson.objects.filter(status='Active').order_by('-reported_at')[:5]
    injured   = InjuredPerson.objects.filter(status='Active').order_by('-reported_at')[:5]
    donation_total  = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    donation_count  = Donation.objects.count()
    context = {
        'disasters':       disasters,
        'missing':         missing,
        'injured':         injured,
        'total_disasters': DisasterReport.objects.count(),
        'total_missing':   MissingPerson.objects.filter(status='Active').count(),
        'total_injured':   InjuredPerson.objects.filter(status='Active').count(),
        'donation_total':  donation_total,
        'donation_count':  donation_count,
    }
    return render(request, 'home.html', context)

def auth_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()

        if not username or not password1:
            messages.error(request, 'Username and password are required.')
            return render(request, 'auth_register.html')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth_register.html')
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'auth_register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'auth_register.html')

        user = User.objects.create_user(
            username=username, email=email,
            password=password1, first_name=first_name
        )
        login(request, user)
        messages.success(request, f'Welcome, {user.first_name or user.username}! Account created.')
        next_url = request.GET.get('next', '/')
        if next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect('home')

    return render(request, 'auth_register.html')


def auth_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/') or '/'
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            if next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
        return render(request, 'auth_login.html', {'next': next_url})
    return render(request, 'auth_login.html', {'next': request.GET.get('next', '/')})


def auth_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

def report_disaster(request):
    if request.method == 'POST':
        disaster_type = request.POST.get('disaster_type', '').strip()
        location      = request.POST.get('location', '').strip()
        description   = request.POST.get('description', '').strip()
        lat           = request.POST.get('latitude', '').strip()
        lng           = request.POST.get('longitude', '').strip()
        photos        = request.FILES.getlist('photos')

        if not disaster_type or not location or not description:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'report_disaster.html')

        avg_people, level = 0, "Unknown"
        resolved_lat = float(lat) if lat else None
        resolved_lng = float(lng) if lng else None

        if resolved_lat and resolved_lng:
            try:
                avg_people, level = get_crowd_for_location(resolved_lat, resolved_lng)
            except Exception as e:
                print(f"Crowd error: {e}")
        elif location:
            try:
                resolved_lat, resolved_lng = geocode_address(location)
                if resolved_lat and resolved_lng:
                    avg_people, level = get_crowd_for_location(resolved_lat, resolved_lng)
            except Exception as e:
                print(f"Geocode error: {e}")

        report = DisasterReport.objects.create(
            disaster_type=disaster_type, location=location,
            latitude=resolved_lat, longitude=resolved_lng,
            estimated_people=avg_people, crowd_level=level,
            description=description,
        )

        for i, photo in enumerate(photos[:10]):
            DisasterPhoto.objects.create(
                disaster=report, photo=photo,
                photo_type=request.POST.get(f'photo_type_{i}', 'during'),
                caption=request.POST.get(f'caption_{i}', ''),
            )

        messages.success(request, 'Disaster report submitted successfully.')
        return redirect('disaster_detail', pk=report.pk)

    return render(request, 'report_disaster.html')

@login_required
def report_missing(request):
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        age        = request.POST.get('age', '').strip()
        gender     = request.POST.get('gender', '').strip()
        location   = request.POST.get('location', '').strip()
        body_marks = request.POST.get('body_marks', '').strip()
        photo      = request.FILES.get('photo')

        if not name or not age or not gender or not location:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'report_missing.html')
        try:
            age = int(age)
            if age < 0 or age > 120:
                raise ValueError
        except ValueError:
            messages.error(request, 'Please enter a valid age.')
            return render(request, 'report_missing.html')

        MissingPerson.objects.create(
            name=name, age=age, gender=gender,
            last_seen_location=location, body_marks=body_marks, photo=photo,
        )
        messages.success(request, 'Missing person report submitted.')
        return redirect('view_missing')

    return render(request, 'report_missing.html')


def view_missing(request):
    persons = MissingPerson.objects.all().order_by('-reported_at')
    paginator = Paginator(persons, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    context = {
        'persons':       page_obj,
        'page_obj':      page_obj,
        'count_active':  persons.filter(status='Active').count(),
        'count_found':   persons.filter(status='Found').count(),
        'count_deceased':persons.filter(status='Deceased').count(),
    }
    return render(request, 'view_missing.html', context)

@login_required
def report_injured(request):
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        age         = request.POST.get('age', '').strip()
        gender      = request.POST.get('gender', '').strip()
        injury_type = request.POST.get('injury_type', '').strip()
        severity    = request.POST.get('severity', '').strip()
        location    = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        photo       = request.FILES.get('photo')

        if not name or not age or not injury_type or not severity or not location:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'report_injured.html')
        try:
            age = int(age)
            if age < 0 or age > 120:
                raise ValueError
        except ValueError:
            messages.error(request, 'Please enter a valid age.')
            return render(request, 'report_injured.html')

        InjuredPerson.objects.create(
            name=name, age=age, gender=gender, injury_type=injury_type,
            severity=severity, location=location, description=description, photo=photo,
        )
        messages.success(request, 'Injured person report submitted.')
        return redirect('view_injured')

    return render(request, 'report_injured.html')


def view_injured(request):
    injured   = InjuredPerson.objects.all().order_by('-reported_at')
    paginator = Paginator(injured, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    context = {
        'injured':        page_obj,
        'page_obj':       page_obj,
        'count_critical': injured.filter(severity='Critical').count(),
        'count_moderate': injured.filter(severity='Moderate').count(),
        'count_minor':    injured.filter(severity='Minor').count(),
    }
    return render(request, 'view_injured.html', context)

@login_required
def update_missing_status(request, pk):
    person = get_object_or_404(MissingPerson, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        note       = request.POST.get('status_note', '').strip()
        valid      = [c[0] for c in MissingPerson.STATUS_CHOICES]
        if new_status in valid and new_status != person.status:
            person.status            = new_status
            person.status_changed_at = timezone.now()
            person.status_note       = note
            person.save()
            messages.success(request, f'Status updated to "{new_status}" for {person.name}.')
        else:
            messages.error(request, 'Invalid or unchanged status.')
    return redirect('view_missing')


@login_required
def update_injured_status(request, pk):
    person = get_object_or_404(InjuredPerson, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        note       = request.POST.get('status_note', '').strip()
        valid      = [c[0] for c in InjuredPerson.STATUS_CHOICES]
        if new_status in valid and new_status != person.status:
            person.status            = new_status
            person.status_changed_at = timezone.now()
            person.status_note       = note
            person.save()
            messages.success(request, f'Status updated to "{new_status}" for {person.name}.')
        else:
            messages.error(request, 'Invalid or unchanged status.')
    return redirect('view_injured')

def donate(request):
    if request.method == 'POST':
        name         = request.POST.get('name', '').strip()
        email        = request.POST.get('email', '').strip()
        amount       = request.POST.get('amount', '').strip()
        purpose      = request.POST.get('purpose', '').strip()
        payment_mode = request.POST.get('payment_mode', '').strip()

        import re as _re
        if not name or not email or not amount or not purpose or not payment_mode:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'donate.html')
        if not _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'donate.html')
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
        except (ValueError, InvalidOperation):
            messages.error(request, 'Please enter a valid donation amount.')
            return render(request, 'donate.html')

        Donation.objects.create(
            name=name, email=email, amount=amount,
            purpose=purpose, payment_mode=payment_mode,
        )
        return render(request, 'donate.html', {
            'donation_success': True,
            'donor_name': name, 'donor_amount': amount,
        })
    return render(request, 'donate.html')


@csrf_exempt
def get_live_population(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data      = json.loads(request.body)
        latitude  = float(data['latitude'])
        longitude = float(data['longitude'])
        radius    = float(data.get('radius', 1))
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid input.'}, status=400)
    try:
        population, level = get_crowd_for_location(latitude, longitude, radius)
        state, city       = reverse_geocode(latitude, longitude)
    except Exception as e:
        return JsonResponse({'error': f'Failed: {str(e)}'}, status=500)
    return JsonResponse({
        'latitude': latitude, 'longitude': longitude, 'radius_km': radius,
        'population': population, 'level': level, 'city': city, 'state': state,
    })


def disaster_detail(request, pk):
    disaster = get_object_or_404(DisasterReport, pk=pk)
    updates  = disaster.updates.all().order_by('-upvotes', '-reported_at')
    photos   = disaster.photos.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'post_update':
            author  = request.POST.get('author_name', '').strip()
            if not author and request.user.is_authenticated:
                author = request.user.get_full_name() or request.user.username
            author  = author or 'Anonymous'
            content = request.POST.get('content', '').strip()
            if content and len(content) <= 500:
                DisasterUpdate.objects.create(
                    disaster=disaster, author_name=author[:100], content=content,
                )
                messages.success(request, 'Update posted.')
            else:
                messages.error(request, 'Update content required (max 500 chars).')
            return redirect('disaster_detail', pk=pk)

        if action == 'upvote':
            update_id   = request.POST.get('update_id')
            update      = get_object_or_404(DisasterUpdate, pk=update_id, disaster=disaster)
            ip          = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0')).split(',')[0].strip()
            _, created  = UpdateUpvote.objects.get_or_create(update=update, ip_address=ip)
            if created:
                update.upvotes += 1
                update.save(update_fields=['upvotes'])
            return JsonResponse({'upvotes': update.upvotes, 'already_voted': not created})

        if action == 'upload_photo':
            photo      = request.FILES.get('photo')
            caption    = request.POST.get('caption', '').strip()
            photo_type = request.POST.get('photo_type', 'during')
            if photo:
                DisasterPhoto.objects.create(
                    disaster=disaster, photo=photo,
                    caption=caption, photo_type=photo_type,
                )
                messages.success(request, 'Photo uploaded.')
            return redirect('disaster_detail', pk=pk)

    return render(request, 'disaster_detail.html', {
        'disaster':      disaster,
        'updates':       updates,
        'photos':        photos,
        'photos_before': photos.filter(photo_type='before'),
        'photos_during': photos.filter(photo_type='during'),
        'photos_after':  photos.filter(photo_type='after'),
        'update_count':  updates.count(),
        'photo_count':   photos.count(),
    })


def disaster_heatmap(request):
    return render(request, 'disaster_heatmap.html')


@csrf_exempt
def heatmap_data(request):
    from django.db.models import Q
    from datetime import timedelta

    dtype = request.GET.get('type', '')
    level = request.GET.get('level', '')
    try:
        days = int(request.GET.get('days', 30))
    except ValueError:
        days = 30

    disasters = DisasterReport.objects.filter(
        latitude__isnull=False, longitude__isnull=False,
        reported_at__gte=timezone.now() - timedelta(days=days)
    )
    if dtype:
        disasters = disasters.filter(disaster_type=dtype)
    if level:
        disasters = disasters.filter(crowd_level=level)

    data = [{
        'id': d.pk, 'lat': d.latitude, 'lng': d.longitude,
        'type': d.disaster_type, 'location': d.location,
        'level': d.crowd_level, 'people': d.estimated_people,
        'reported_at': d.reported_at.strftime('%d %b %Y, %H:%M'),
        'url': f'/disasters/{d.pk}/', 'description': d.description[:120],
    } for d in disasters]

    all_d = DisasterReport.objects.filter(latitude__isnull=False, longitude__isnull=False)
    return JsonResponse({
        'points': data, 'total': len(data),
        'stats': {
            'fire':       all_d.filter(disaster_type='Fire').count(),
            'flood':      all_d.filter(disaster_type='Flood').count(),
            'earthquake': all_d.filter(disaster_type='Earthquake').count(),
            'cyclone':    all_d.filter(disaster_type='Cyclone').count(),
            'other':      all_d.exclude(disaster_type__in=['Fire','Flood','Earthquake','Cyclone']).count(),
        }
    })


def view_disasters(request):
    q     = request.GET.get('q', '').strip()
    dtype = request.GET.get('type', '').strip()
    level = request.GET.get('level', '').strip()

    disasters = DisasterReport.objects.order_by('-reported_at')
    if q:
        from django.db.models import Q
        disasters = disasters.filter(
            Q(location__icontains=q) | Q(description__icontains=q) | Q(disaster_type__icontains=q)
        )
    if dtype:
        disasters = disasters.filter(disaster_type=dtype)
    if level:
        disasters = disasters.filter(crowd_level=level)

    total     = disasters.count()
    paginator = Paginator(disasters, 12)
    page_obj  = paginator.get_page(request.GET.get('page'))

    all_d = DisasterReport.objects.all()
    return render(request, 'view_disasters.html', {
        'disasters': page_obj, 'page_obj': page_obj,
        'query': q, 'filter_type': dtype, 'filter_level': level, 'total': total,
        'disaster_types':   all_d.values_list('disaster_type', flat=True).distinct(),
        'count_fire':       all_d.filter(disaster_type='Fire').count(),
        'count_flood':      all_d.filter(disaster_type='Flood').count(),
        'count_earthquake': all_d.filter(disaster_type='Earthquake').count(),
        'count_cyclone':    all_d.filter(disaster_type='Cyclone').count(),
        'count_other':      all_d.exclude(disaster_type__in=['Fire','Flood','Earthquake','Cyclone']).count(),
    })

def submit_feedback(request):
    if request.method == 'POST':
        feedback_type  = request.POST.get('feedback_type', 'other')
        content_type   = request.POST.get('content_type', 'general')
        object_id      = request.POST.get('object_id', '').strip()
        reporter_name  = request.POST.get('reporter_name', '').strip()
        reporter_email = request.POST.get('reporter_email', '').strip()
        message        = request.POST.get('message', '').strip()

        if request.user.is_authenticated:
            if not reporter_name:
                reporter_name = request.user.get_full_name() or request.user.username
            if not reporter_email:
                reporter_email = request.user.email

        if not message:
            messages.error(request, 'Please describe the issue.')
            return render(request, 'feedback.html', request.POST)

        Feedback.objects.create(
            feedback_type  = feedback_type,
            content_type   = content_type,
            object_id      = int(object_id) if object_id.isdigit() else None,
            reporter_name  = reporter_name or 'Anonymous',
            reporter_email = reporter_email,
            message        = message,
        )
        messages.success(request, 'Thank you! Your feedback has been submitted.')
        return redirect(request.POST.get('next', 'home'))

    return render(request, 'feedback.html', {
        'prefill_type':  request.GET.get('content_type', 'general'),
        'prefill_id':    request.GET.get('object_id', ''),
        'next':          request.GET.get('next', '/'),
    })


@login_required
def admin_dashboard(request):
    from django.db.models import Count

    donation_total = float(Donation.objects.aggregate(total=Sum('amount'))['total'] or 0)

    disaster_by_type = list(
        DisasterReport.objects.values('disaster_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    disaster_by_level = list(
        DisasterReport.objects.values('crowd_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    missing_by_status = {
        s: MissingPerson.objects.filter(status=s).count()
        for s in ['Active', 'Found', 'Deceased']
    }
    injured_by_status = {
        s: InjuredPerson.objects.filter(status=s).count()
        for s in ['Active', 'Recovering', 'Discharged']
    }
    injured_by_severity = {
        s: InjuredPerson.objects.filter(severity=s).count()
        for s in ['Critical', 'Moderate', 'Minor']
    }
    recent_disasters = DisasterReport.objects.order_by('-reported_at')[:8]
    recent_missing   = MissingPerson.objects.order_by('-reported_at')[:5]
    recent_injured   = InjuredPerson.objects.order_by('-reported_at')[:5]
    recent_donations = Donation.objects.order_by('-id')[:5]

    return render(request, 'admin_dashboard.html', {
        'total_disasters':    DisasterReport.objects.count(),
        'total_missing':      MissingPerson.objects.count(),
        'active_missing':     missing_by_status['Active'],
        'total_injured':      InjuredPerson.objects.count(),
        'critical_injured':   injured_by_severity['Critical'],
        'total_donations':    Donation.objects.count(),
        'donation_total':     donation_total,
        'pending_feedback':   Feedback.objects.filter(resolved=False).count(),
        'disaster_by_type':   disaster_by_type,
        'disaster_by_level':  disaster_by_level,
        'missing_by_status':  missing_by_status,
        'injured_by_status':  injured_by_status,
        'injured_by_severity': injured_by_severity,
        'recent_disasters':   recent_disasters,
        'recent_missing':     recent_missing,
        'recent_injured':     recent_injured,
        'recent_donations':   recent_donations,
        'recent_feedback':    Feedback.objects.filter(resolved=False).order_by('-submitted_at')[:8],
    })


@login_required
def resolve_feedback(request, pk):
    if request.method == 'POST':
        fb = get_object_or_404(Feedback, pk=pk)
        fb.resolved = True
        fb.save()
        messages.success(request, f'Feedback #{pk} marked as resolved.')
    return redirect('admin_dashboard')