# 🔴 DisasterNet

> **Crowd-Source Disaster Management Platform**  
> Real-time disaster reporting, missing persons tracking, injured persons management, and emergency coordination — built with Django.

![Version](https://img.shields.io/badge/version-2.7.0-red)
![Django](https://img.shields.io/badge/Django-4.2-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [URL Reference](#url-reference)
- [Models](#models)
- [API Endpoints](#api-endpoints)
- [PWA Support](#pwa-support)
- [Screenshots](#screenshots)
- [Team](#team)

---

## Overview

DisasterNet is a community-driven disaster management web application that allows citizens to report disasters, track missing and injured persons, and coordinate emergency response — all in real time. The platform features a live heatmap, crowd-density estimation, photo evidence upload, and a multi-language interface.

---

## Features

### 🗺️ Disaster Reporting
- Report disasters with type, location (GPS or map pin), affected area radius, and crowd estimate
- Photo evidence upload with multiple photos per report
- Community update system with upvote/downvote per update (IP-based deduplication)
- Detailed disaster page with survival guide and emergency action tips
- Share to WhatsApp, Twitter, and clipboard

### 🔥 Live Heatmap
- Interactive Leaflet.js map with CARTO Dark Matter tiles
- Colour-coded circle markers sized by crowd intensity
- Filter by disaster type, severity level, and date range
- Auto-refreshes every 30 seconds
- Real-time coordinate tracker on hover

### 🧍 Missing Persons
- Report missing persons with photo, physical description, last seen location
- Search and filter by name, location, status, and gender
- Status management: Active → Found / Deceased (staff only)
- Status notes and timestamp tracking

### 🏥 Injured Persons
- Report injured persons with injury type, severity, and location
- Severity levels: Minor, Moderate, Critical
- Status management: Active → Recovering / Discharged (staff only)

### 💰 Donations
- Track donations with purpose categorisation
- Multiple payment modes supported
- Donation total displayed on home page

### 📊 Admin Dashboard
- Disaster breakdown by type and crowd level
- Missing/injured persons status summary
- Recent activity feeds (disasters, missing, injured, donations)
- Unresolved feedback queue

### 🌐 Multi-language Support
- English, Hindi (हिन्दी), and Odia (ଓଡ଼ିଆ) via client-side translation
- Language preference saved to localStorage
- FAB (floating action button) switcher on all pages

### 📱 Progressive Web App (PWA)
- Installable on Android and iOS
- Service worker with offline caching
- App manifest with icons and theme colour

### 🔒 Authentication
- Register, login, and logout
- Avatar dropdown with user menu
- `@login_required` on sensitive write operations
- Staff-only access for status updates and admin dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 (Python) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Maps | Leaflet.js + OpenStreetMap / CARTO |
| Geocoding | Nominatim (OpenStreetMap) |
| Frontend | Vanilla JS, CSS custom properties |
| Fonts | Rajdhani, DM Sans (Google Fonts) |
| Icons | Heroicons (inline SVG) |
| Images | Pillow (ImageField) |
| HTTP | requests (geocoding API calls) |
| PWA | Web App Manifest + Service Worker |

---

## Project Structure

```
disasternet/
├── manage.py
├── requirements.txt
├── db.sqlite3
│
├── core/              
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py              
│   └── wsgi.py
│
├── reports/                  
│   ├── models.py            
│   ├── views.py              
│   ├── urls.py               
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py      
│   └── utils.py            
│
├── templates/
│   ├── base.html            
│   ├── home.html
│   ├── report_disaster.html
│   ├── report_missing.html
│   ├── report_injured.html
│   ├── view_disasters.html
│   ├── view_missing.html
│   ├── view_injured.html
│   ├── disaster_detail.html
│   ├── disaster_heatmap.html
│   ├── admin_dashboard.html
│   ├── donate.html
│   ├── feedback.html
│   ├── auth_login.html
│   ├── auth_register.html
│   └── pagination.html
│
├── static/
│   ├── manifest.json         
│   ├── sw.js                 
│   └── icons/                
│
└── media/                    
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

---

## Configuration

All configuration is in `disasternet/settings.py`.

| Setting | Default | Description |
|---|---|---|
| `DEBUG` | `True` | Set to `False` in production |
| `SECRET_KEY` | Dev key |
| `DATABASES` | SQLite |
| `MEDIA_ROOT` | `media/` | Uploaded files directory |
| `STATIC_ROOT` | `staticfiles/` | Collected static files |
| `LOGIN_URL` | `/auth/login/` | Redirect for unauthenticated access |
| `LOGIN_REDIRECT_URL` | `/` | Redirect after login |
| `LOGOUT_REDIRECT_URL` | `/` | Redirect after logout |

### Media Files (Development)

Add the following to your project-level `urls.py` for serving uploaded photos locally:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
---

## URL Reference

| URL | View | Login Required | Description |
|---|---|---|---|
| `/` | `home` | No | Home page with stats and map |
| `/report/` | `report_disaster` | No | Submit a disaster report |
| `/disasters/` | `view_disasters` | No | Browse all disaster reports |
| `/disasters/<id>/` | `disaster_detail` | No | Disaster detail with survival guide |
| `/heatmap/` | `disaster_heatmap` | No | Live interactive heatmap |
| `/missing/report/` | `report_missing` | Yes | Report a missing person |
| `/missing/view/` | `view_missing` | No | Browse missing persons |
| `/missing/<id>/update-status/` | `update_missing_status` | Yes (staff) | Update found/deceased status |
| `/injured/report/` | `report_injured` | Yes | Report an injured person |
| `/injured/view/` | `view_injured` | No | Browse injured persons |
| `/injured/<id>/update-status/` | `update_injured_status` | Yes (staff) | Update recovery status |
| `/donate/` | `donate` | No | Donation form |
| `/feedback/` | `submit_feedback` | No | Submit feedback |
| `/feedback/<id>/resolve/` | `resolve_feedback` | Yes (staff) | Mark feedback resolved |
| `/admin-dashboard/` | `admin_dashboard` | Yes (staff) | Admin overview |
| `/auth/register/` | `auth_register` | No | User registration |
| `/auth/login/` | `auth_login` | No | User login |
| `/auth/logout/` | `auth_logout` | Yes | User logout |

---

## Models

### `DisasterReport`
| Field | Type | Notes |
|---|---|---|
| `disaster_type` | CharField | Fire, Flood, Earthquake, Cyclone, Landslide, Tsunami, Accident, Chemical Spill, Other |
| `location` | CharField | Place name |
| `latitude` / `longitude` | FloatField | GPS coordinates (optional) |
| `estimated_people` | IntegerField | Crowd count estimate |
| `crowd_level` | CharField | Minimal / Low / Moderate / High / Critical / Unknown |
| `description` | TextField | Free-text description |
| `reported_at` | DateTimeField | Auto-set on creation |

### `DisasterPhoto`
| Field | Type | Notes |
|---|---|---|
| `disaster` | ForeignKey | → DisasterReport |
| `photo` | ImageField | Stored in `media/` |
| `caption` | CharField | Optional caption |
| `photo_type` | CharField | Scene / Aerial / Rescue / Before / After / Other |

### `DisasterUpdate`
| Field | Type | Notes |
|---|---|---|
| `disaster` | ForeignKey | → DisasterReport |
| `author_name` | CharField | Display name |
| `content` | TextField | Update text |
| `upvotes` | IntegerField | Upvote count |

### `MissingPerson`
| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Full name |
| `age` | IntegerField | Age |
| `gender` | CharField | Male / Female / Other |
| `last_seen_location` | CharField | Location text |
| `body_marks` | TextField | Identifying features |
| `photo` | ImageField | Optional photo |
| `status` | CharField | Active / Found / Deceased |
| `status_changed_at` | DateTimeField | Nullable, set on status change |
| `status_note` | TextField | Reason / detail for status change |

### `InjuredPerson`
| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Full name |
| `age` | IntegerField | Age |
| `injury_type` | CharField | Type of injury |
| `severity` | CharField | Minor / Moderate / Critical |
| `location` | CharField | Where found |
| `status` | CharField | Active / Recovering / Discharged |
| `status_changed_at` | DateTimeField | Nullable, set on status change |
| `status_note` | TextField | Reason / detail for status change |

### `Donation`
| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Donor name |
| `email` | EmailField | Donor email |
| `amount` | DecimalField | Amount donated |
| `purpose` | CharField | Disaster Relief / Medical / Food / Shelter / Other |
| `payment_mode` | CharField | UPI / Bank Transfer / Cash / Other |

### `Feedback`
| Field | Type | Notes |
|---|---|---|
| `feedback_type` | CharField | Bug / Incorrect Info / Missing Data / Other |
| `content_type` | CharField | Disaster / Missing / Injured / General |
| `object_id` | IntegerField | ID of the related object (optional) |
| `reporter_name` | CharField | Submitter name |
| `message` | TextField | Feedback content |
| `resolved` | BooleanField | Default False |

---

## API Endpoints

### `GET /api/heatmap-data/`

Returns disaster points for the live heatmap.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `type` | string | (all) | Filter by disaster type |
| `level` | string | (all) | Filter by crowd level |
| `days` | integer | 30 | Number of past days to include |

**Response:**

```json
{
  "total": 42,
  "stats": {
    "fire": 8,
    "flood": 12,
    "earthquake": 3,
    "cyclone": 2,
    "other": 17
  },
  "points": [
    {
      "lat": 20.29,
      "lng": 85.82,
      "type": "Flood",
      "level": "High",
      "location": "Cuttack, Odisha",
      "description": "Flash flood near Mahanadi...",
      "reported_at": "2 hours ago",
      "url": "/disasters/7/"
    }
  ]
}
```

### `GET /get-live-population/`

Returns live crowd/population estimate for a given coordinate and radius.

**Query Parameters:** `lat`, `lng`, `radius_km`

---

## PWA Support

DisasterNet is installable as a Progressive Web App on Android and iOS.

**Setup:**

1. Place `manifest.json` and `sw.js` in the `static/` directory
2. Add icon files at `static/icons/icon-192.png` and `static/icons/icon-512.png`
3. Run `python manage.py collectstatic`

The service worker automatically caches pages and skips non-GET requests, `/admin/`, `/api/`, and `/get-live-population/` routes.

---

## Screenshots

| Page | Description |
|---|---|
| Home | Hero section, live stats, population estimator map |
| Live Heatmap | Full-screen tactical map with sidebar controls |
| Disaster Detail | Report detail, photo gallery, survival guide, community updates |
| Admin Dashboard | Stats grid, recent activity, feedback queue |

---

## Team

Built as a college project by:

| Name | Role |
|---|---|
| **Mohd Sharib** |
| **Sephali Chandrakar** |
| **Antaryami Swain** |

---

## License

This project is licensed under the MIT License.

---

> DisasterNet v2.7.0 · [GitHub](https://github.com/knight-styles/disaster-net)
