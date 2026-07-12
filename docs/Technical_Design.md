# UrbanSense

> Technical Design Document (TDD)

---

## Document Information

| Field | Value |
|--------|-------|
| Project | UrbanSense |
| Version | 1.0 |
| Status | Draft |
| Last Updated | 9 July 2026 |
| Related Document | PRD.md |

---

# 1. System Overview

UrbanSense is a cloud-based AI-powered urban air quality intelligence platform designed to assist municipal authorities in monitoring, analyzing, forecasting, and responding to urban air pollution.

The platform integrates environmental observations, weather information, geospatial datasets, and artificial intelligence into a unified decision-support system.

Unlike traditional AQI dashboards, UrbanSense focuses on transforming environmental data into actionable intelligence by identifying pollution hotspots, estimating pollution sources, forecasting AQI, recommending interventions, tracking administrative actions, and generating citizen advisories.

The system follows a modular architecture that separates data ingestion, intelligence generation, business logic, and presentation layers, enabling independent development and future scalability.

---

# 2. High-Level Architecture

UrbanSense follows a layered architecture consisting of five logical layers.

```text
                    Users
                       │
                       ▼
              React Frontend
                       │
                REST API (FastAPI)
                       │
      ┌────────────────┼─────────────────┐
      │                │                 │
      ▼                ▼                 ▼
Business Logic    AI Intelligence    Geospatial Engine
      │                │                 │
      └────────────────┼─────────────────┘
                       │
                Supabase Database
                       │
         External APIs & Public Datasets
```

### Architectural Principles

- Modular Design
- API-First Development
- Separation of Concerns
- AI-Assisted Decision Support
- Explainable Intelligence
- Scalable Cloud Deployment

---

# 3. Technology Stack

## Frontend

| Technology | Purpose |
|------------|---------|
| React | User Interface |
| Vite | Build Tool |
| TypeScript | Type Safety |
| Tailwind CSS | Styling |
| shadcn/ui | UI Components |
| React Router | Routing |
| React Query (TanStack Query) | Server State Management |
| React Leaflet | Interactive Maps |
| Recharts | Charts & Analytics |

---

## Backend

| Technology | Purpose |
|------------|---------|
| FastAPI | REST API |
| Python | Backend Language |
| SQLAlchemy | ORM |
| Alembic | Database Migrations |
| Pydantic | Validation |
| Uvicorn | ASGI Server |

---

## Database

| Technology | Purpose |
|------------|---------|
| Supabase (PostgreSQL) | Primary Database |
| PostGIS | Geospatial Queries (via Supabase) |

---

## AI Components

| Technology | Purpose |
|------------|---------|
| Gemini API | AI Explanations & Recommendations |
| Scikit-learn | Forecasting Models |
| Pandas | Data Processing |
| NumPy | Numerical Computation |

---

## Geospatial

| Technology | Purpose |
|------------|---------|
| OpenStreetMap | Base Map |
| GeoJSON | Ward Boundaries |
| React Leaflet | Map Rendering |
| PostGIS | Spatial Analysis |

---

## Development

| Technology | Purpose |
|------------|---------|
| Git | Version Control |
| GitHub | Repository |
| Docker | Containerization |
| Render / Railway | Deployment |

---
# 4. Project Structure

UrbanSense follows a **feature-based modular architecture**. Each business capability is implemented as an independent module containing its own frontend components, backend services, APIs, models, and business logic.

This architecture improves maintainability, scalability, and allows AI-assisted development tools to generate code for individual modules without affecting unrelated parts of the system.

## Repository Structure

```text
urbansense/

├── docs/
│   ├── PRD.md
│   ├── Technical_Design.md
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── lib/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── features/
│   │   │
│   │   ├── dashboard/
│   │   ├── city-map/
│   │   ├── ward/
│   │   ├── analytics/
│   │   ├── forecasting/
│   │   ├── interventions/
│   │   ├── communication/
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   └── public/
│
├── backend/
│   ├── app/
│   │
│   │   ├── core/
│   │   ├── config/
│   │   ├── database/
│   │   ├── shared/
│   │   │
│   │   ├── modules/
│   │   │
│   │   ├── dashboard/
│   │   ├── city_map/
│   │   ├── ward/
│   │   ├── analytics/
│   │   ├── forecasting/
│   │   ├── interventions/
│   │   ├── communication/
│   │   │
│   │   └── main.py
│
├── datasets/
│
├── scripts/
│
├── docker/
│
├── .github/
│
├── docker-compose.yml
│
└── README.md
```

## Architectural Principles

UrbanSense follows the following design principles:

- Feature-first organization
- Separation of concerns
- Modular development
- Reusable shared components
- API-first communication
- Explainable AI integration
- Scalable cloud deployment

## Naming Conventions

### Frontend

- Components: PascalCase
- Hooks: useCamelCase
- APIs: feature.api.ts
- Types: feature.types.ts

### Backend

- Routers: snake_case
- Services: snake_case
- Models: snake_case
- Schemas: snake_case

### APIs

- RESTful endpoints
- Versioned under `/api/v1`
- JSON request/response format

---

# 5. Product Modules

UrbanSense is organized into seven core product modules. Each module represents a major business capability within the platform and is designed to operate independently while communicating through shared backend services and REST APIs.

This modular architecture improves maintainability, scalability, and enables parallel development across frontend, backend, and AI components.

## Core Product Modules

| Module | Purpose | Primary Users |
|----------|---------|---------------|
| AI Command Dashboard | Provides a city-wide operational overview, environmental KPIs, alerts, and system status. | Municipal Administrators |
| Interactive City Map | Visualizes ward boundaries, AQI heatmaps, pollution hotspots, monitoring stations, and critical infrastructure. | Municipal Administrators |
| Ward Intelligence Panel | Displays detailed environmental insights, historical trends, and contextual information for a selected ward. | Pollution Control Officers |
| Pollution Analytics Engine | Analyzes environmental data to identify pollution patterns, estimate probable pollution sources, and generate explainable insights. | Municipal Administrators |
| AQI Forecasting Center | Predicts short-term air quality conditions using historical observations and weather forecasts. | Municipal Administrators |
| Recommendation & Intervention Center | Generates AI-assisted recommendations, records administrative interventions, and tracks post-intervention outcomes. | Municipal Administrators |
| Communication & Reporting Center | Generates citizen advisories, administrative reports, and decision-support documentation. | Municipal Administrators |

## Module Interaction Flow

```text
AI Command Dashboard
          │
          ▼
Interactive City Map
          │
          ▼
Ward Intelligence Panel
          │
          ▼
Pollution Analytics Engine
          │
          ▼
AQI Forecasting Center
          │
          ▼
Recommendation & Intervention Center
          │
          ▼
Communication & Reporting Center
```

## Shared Platform Services

The following services are shared across all modules:

- Authentication & Authorization
- User & Role Management
- Configuration Management
- Logging & Monitoring
- External API Integration
- AI Provider Integration
- File Storage
- Notification Services

Detailed functional specifications and implementation details for each module are documented separately in the project implementation documents.

---

# 6. Data Sources

UrbanSense integrates multiple environmental datasets and external APIs to provide comprehensive urban air quality intelligence. The platform adopts a hybrid data integration strategy that combines publicly available datasets with simulated data where real-time information is unavailable.

## Data Source Overview

| Data Source | Purpose | Type | MVP |
|-------------|---------|------|-----|
| CPCB Air Quality Data | Current and historical AQI observations | Public Dataset | ✅ |
| OpenWeatherMap API | Weather conditions and forecasts | External API | ✅ |
| OpenStreetMap | Interactive base maps | Open Dataset | ✅ |
| GeoJSON Ward Boundaries | Administrative boundaries | Open Dataset | ✅ |
| Historical AQI Dataset | Forecasting and trend analysis | Public Dataset | ✅ |
| Traffic Density | Pollution source attribution | Simulated | ✅ |
| Construction Activity | Dust emission estimation | Simulated | ✅ |
| Industrial Zones | Emission source mapping | Simulated | ✅ |
| Schools & Hospitals | Vulnerable population mapping | Open Dataset | Optional |

## Data Integration Strategy

UrbanSense follows a layered data integration approach:

```text
Public Datasets
        │
External APIs
        │
Simulated Data
        │
        ▼
Data Collection Layer
        │
        ▼
Data Validation & Transformation
        │
        ▼
Supabase (PostgreSQL + PostGIS)
        │
        ▼
AI Processing Layer
        │
        ▼
REST APIs
        │
        ▼
Frontend Dashboard
```

## Design Principles

The platform follows the following principles when integrating external data:

- Prefer trusted public data sources whenever available.
- Use simulated datasets only where official data is inaccessible.
- Keep raw environmental observations separate from AI-generated insights.
- Design all data connectors to be replaceable with official production APIs in future versions.
- Ensure the platform remains extensible as additional environmental datasets become available.

Detailed dataset specifications, schemas, preprocessing pipelines, and update mechanisms are documented separately in the implementation documentation.

---

# 7. System Data Flow

UrbanSense follows a structured data pipeline that transforms raw environmental observations into actionable intelligence for city administrators.

## End-to-End Data Flow

```text
                External Data Sources
 ┌──────────────────────────────────────────────────┐
 │ CPCB AQI │ Weather API │ OSM │ GeoJSON │ Simulated Data │
 └──────────────────────────────────────────────────┘
                         │
                         ▼
               Data Collection Layer
                         │
                         ▼
          Validation & Data Transformation
                         │
                         ▼
             Supabase (PostgreSQL + PostGIS)
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 Business Logic     AI Processing     Analytics Engine
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                    REST API Layer
                         │
                         ▼
                 React Web Application
                         │
                         ▼
            Municipal Administrators
```

## Processing Pipeline

1. Collect environmental data from external sources.
2. Validate and normalize incoming data.
3. Store raw observations in Supabase (PostgreSQL).
4. Process data using AI and analytics services.
5. Expose processed information through REST APIs.
6. Visualize intelligence through the frontend dashboard.
7. Record administrative interventions for future analysis.

---

# 8. Security & Authentication

UrbanSense follows industry-standard security practices to protect system access and environmental data.

## Authentication

- JWT-based authentication
- Secure password hashing
- Session expiration
- Protected API routes

## Authorization

Role-Based Access Control (RBAC)

Roles:

- Super Administrator
- Municipal Administrator
- Pollution Control Officer

## Security Principles

- HTTPS communication
- Environment variable management
- API request validation
- Input sanitization
- Centralized error handling
- Audit logging

---

# 9. Deployment Architecture

UrbanSense is designed as a cloud-native web application.

## Deployment Diagram

```text
                 React Frontend
                (Vercel / Netlify)
                       │
                       ▼
                 FastAPI Backend
              (Render / Railway)
                       │
                       ▼
               Supabase Database
            (PostgreSQL + PostGIS)
                       │
                       ▼
               External APIs & Datasets
```

## Deployment Principles

- Independent frontend and backend deployments
- Environment-based configuration
- Scalable cloud infrastructure
- Automated CI/CD support

---

# 10. Non-Functional Requirements

UrbanSense is designed to satisfy key quality attributes expected from a modern decision-support platform.

## Performance

- Dashboard loads within 3 seconds.
- Map interactions remain responsive.
- API response time under 500 ms for common requests.

## Scalability

- Modular architecture supports additional cities and datasets.
- APIs are stateless for horizontal scaling.

## Reliability

- Graceful handling of unavailable external APIs.
- Robust error logging and monitoring.

## Security

- Role-based access control.
- Secure API communication.
- Protected environment secrets.

## Maintainability

- Feature-based project structure.
- Reusable UI components.
- Modular backend services.

## Usability

- Responsive web interface.
- Clear data visualizations.
- Intuitive navigation for administrators.

## Extensibility

The architecture allows future integration of:

- Live IoT sensors
- Satellite imagery
- Government GIS services
- Mobile applications
- Citizen notification channels