# UrbanSense Data Integration

## 1. Purpose

This document defines the complete data integration strategy for UrbanSense.

It serves as the implementation guide for integrating external APIs, public datasets, geospatial information, weather services, and AI processing pipelines into the UrbanSense platform.

The objective is to ensure that every data source follows a consistent architecture, remains replaceable, and can scale as additional cities and datasets are added.

This document is intended for both developers and AI-assisted development tools and should be referenced before implementing any backend services, data pipelines, or external API integrations.

## 2. Data Integration Philosophy

UrbanSense is designed around a modular data integration architecture.

Rather than tightly coupling the application to a specific dataset or API, every external source is treated as an independent provider that can be replaced or extended without affecting the rest of the system.

The platform follows the following principles:

- Prefer official government datasets whenever available.
- Prefer live APIs over manually updated datasets whenever possible.
- Store normalized data inside Supabase instead of directly querying external APIs from the frontend.
- Keep raw observations separate from AI-generated insights.
- Cache frequently used data to minimize unnecessary API requests.
- Gracefully handle unavailable or incomplete datasets.
- Design every integration to support multiple Indian cities.
- Allow new datasets to be added without changing the frontend architecture.

## 3. Supported Cities Strategy

UrbanSense is designed as a nationwide platform capable of supporting urban air quality monitoring across India.

Instead of being developed for a single city, the platform follows a city-agnostic architecture where every supported city shares the same application workflow, database schema, APIs, and AI services.

### City Selection Workflow

The dashboard provides a searchable city selector positioned in the top navigation.

Administrators can search for any supported Indian city by name.

Example:

```text
🔍 Search City

Delhi

Mumbai

Bengaluru

Hyderabad

Chennai

Ahmedabad
```

Once a city is selected, the platform dynamically loads:

- Air quality observations
- Weather information
- AQI monitoring stations
- Ward boundaries (when available)
- Historical trends
- Forecasting models
- AI recommendations
- Citizen advisories

No page reload is required. The dashboard updates dynamically based on the selected city.

### Dynamic City Registration & Geocoding Workflow

To avoid pre-seeding thousands of cities manually, the platform dynamically resolves and registers new cities when searched:

1. **Search & Database Check**: When a user searches for an Indian city, the backend first checks the local database.
2. **Geocoding Resolution**: If not found locally, the backend calls the OpenWeatherMap Geocoding API (or OpenStreetMap Nominatim) to fetch the coordinates (latitude, longitude) of the requested city in India.
3. **Database Insertion**: The new city is dynamically registered in the database `cities` table, marking it as `Level 1` (has_wards = false).
4. **Data Initialization**: The backend automatically initializes a simulated monitoring station and loads current weather and AQI observations for the new coordinates.
5. **Dashboard Render**: The frontend receives the newly registered city object and displays the operational dashboard.

### Progressive Intelligence Strategy

UrbanSense supports two levels of intelligence.

#### Level 1 – City-Level Intelligence
Available dynamically for **every** searched city in India via geocoding.
Features include:
- AQI dashboard
- Weather information
- AQI forecasting
- AI recommendations
- Historical trends
- Citizen advisories

#### Level 2 – Ward-Level Intelligence
Available only for pre-configured cities with detailed geospatial datasets (e.g., Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Ahmedabad).
Additional capabilities include:
- Ward boundaries
- Heatmaps
- Pollution hotspot analysis
- Ward analytics
- Sensitive infrastructure overlays
- Hyperlocal recommendations

If ward-level datasets are unavailable for a selected city, the platform automatically falls back to city-level analytics while keeping all remaining functionality operational.

This approach allows UrbanSense to scale across India while accommodating differences in data availability between cities.

## 4. Master Data Integration Matrix

The following table defines every external data source used by UrbanSense during the MVP.

Each integration specifies the source, whether the data is live or static, how it is stored, refresh frequency, and the fallback strategy if the source becomes unavailable.

| Component             | Data Source                        | Type               | Storage             | Refresh Strategy                  | Fallback Strategy                 | MVP      |
| --------------------- | ---------------------------------- | ------------------ | ------------------- | --------------------------------- | --------------------------------- | -------- |
| Air Quality (AQI)     | CPCB CAAQMS                        | Live API / Dataset | Supabase            | Every 1 hour                      | Use latest cached observation     | ✅        |
| Weather               | OpenWeatherMap API                 | Live API           | Supabase Cache      | Every 1–3 hours                   | Use previous successful forecast  | ✅        |
| Interactive Maps      | OpenStreetMap                      | Live Tile Service  | Client Side         | On Demand                         | None                              | ✅        |
| Ward Boundaries       | Government GeoJSON / Open Datasets | Static Dataset     | Supabase Storage    | Manual Updates                    | Switch to City-Level Analytics    | ✅        |
| Historical AQI        | CPCB Historical Dataset            | Static Dataset     | Supabase            | Initial Import + Periodic Updates | Existing Historical Records       | ✅        |
| Traffic Density       | Simulated Dataset                  | Static Dataset     | Supabase            | Manual                            | Assume Moderate Traffic           | ✅        |
| Construction Activity | Simulated Dataset                  | Static Dataset     | Supabase            | Manual                            | Ignore Construction Contribution  | ✅        |
| Industrial Zones      | Government/Open GIS Dataset        | Static Dataset     | Supabase            | Manual                            | Skip Industrial Attribution       | ✅        |
| Hospitals & Schools   | OpenStreetMap / Government GIS     | Static Dataset     | Supabase            | Rare                              | Hide Vulnerability Layer          | Optional |
| AI Recommendations    | Groq API                           | Live API           | Generated On Demand | Every User Request                | Display Rule-Based Recommendation | ✅        |
| AQI Forecast          | Forecasting Model (FastAPI)        | Generated          | Supabase            | On Demand / Scheduled             | Use Latest Prediction             | ✅        |
| Reports               | Generated by Backend               | Generated          | Supabase Storage    | On Demand                         | Allow Manual Export               | Optional |

### Integration Principles

Every data integration within UrbanSense follows these principles:

* Official government datasets are preferred whenever available.
* Live APIs should never be called directly from the frontend.
* All external data should pass through the backend before reaching the client.
* Frequently accessed data should be cached to reduce API usage and improve performance.
* Static datasets should be imported into Supabase instead of being fetched repeatedly.
* AI-generated insights must always be stored separately from raw environmental observations.
* Every integration should support multiple Indian cities without requiring frontend changes.
* The application should continue functioning even if optional datasets become unavailable.

## 5. External Data Sources

UrbanSense integrates multiple external data providers to deliver comprehensive air quality intelligence. Each data source is responsible for a specific aspect of the platform and is integrated through the backend to ensure security, consistency, and scalability.

---

### 5.1 CPCB Air Quality Data (CAAQMS observations)

#### Purpose

The Central Pollution Control Board (CPCB) is the primary source of air quality observations for UrbanSense.

It provides official monitoring data collected from Continuous Ambient Air Quality Monitoring Stations (CAAQMS) deployed across Indian cities.

#### Data Collected

* Air Quality Index (AQI)
* PM2.5
* PM10
* NO₂
* SO₂
* CO
* O₃
* Monitoring Station Name
* Timestamp
* City

#### Used By

* Dashboard
* Interactive Map
* Ward Intelligence
* Historical Trends
* AQI Forecasting
* Pollution Analytics
* AI Recommendation Engine

#### Storage Strategy

Raw observations are stored in Supabase.

Processed analytics and AI insights are stored separately to preserve data integrity.

#### Refresh Strategy

* Scheduled synchronization every hour
* Manual refresh supported for administrators

#### Fallback Strategy

If CPCB data becomes temporarily unavailable:

* Display the latest cached observations.
* Notify administrators that live data is temporarily unavailable.
* Continue AI analysis using cached records.

---

### 5.2 OpenWeatherMap API

#### Purpose

Weather conditions significantly influence pollution dispersion. UrbanSense integrates weather forecasts to improve AQI forecasting accuracy and provide contextual environmental insights.

#### Data Collected

* Temperature
* Humidity
* Wind Speed
* Wind Direction
* Atmospheric Pressure
* Visibility
* Rainfall (if available)

#### Used By

* Dashboard
* Forecasting Engine
* AI Recommendation Engine

#### Storage Strategy

Weather responses are cached in Supabase to minimize unnecessary API requests.

#### Refresh Strategy

Every 1–3 hours depending on forecast availability.

#### Fallback Strategy

Use the most recent successful forecast until fresh data becomes available.

---

### 5.3 OpenStreetMap

#### Purpose

OpenStreetMap provides the base map used throughout the application.

#### Data Used

* Road Network
* Administrative Locations
* Geographic Coordinates
* Landmarks

#### Used By

* Interactive City Map
* Ward Visualization
* Pollution Hotspots

#### Storage Strategy

Map tiles are loaded directly in the frontend.

No permanent storage is required.

#### Refresh Strategy

Loaded on demand by the client application.

---

### 5.4 GeoJSON Administrative Boundaries

#### Purpose

GeoJSON files define city and ward boundaries used for geospatial visualization.

#### Data Included

* City Boundaries
* Ward Boundaries
* Polygon Coordinates
* Administrative Metadata

#### Used By

* Interactive Map
* Ward Intelligence
* Heatmaps
* Geospatial Analytics

#### Storage Strategy

GeoJSON files are stored in Supabase Storage and cached by the frontend.

#### Refresh Strategy

Manual updates whenever revised datasets become available.

#### Fallback Strategy

If ward-level boundaries are unavailable, the application automatically switches to city-level analytics.

---

### 5.5 Groq API

#### Purpose

Groq powers the explainable AI capabilities of UrbanSense.

It does not generate raw environmental data. Instead, it interprets analytical results and produces human-readable recommendations.

#### Responsibilities

* Pollution source explanation
* Intervention recommendations
* Citizen health advisories
* Environmental summaries
* Administrative reports

#### Inputs

* AQI observations
* Weather information
* Forecast results
* Historical trends
* Pollution analytics

#### Outputs

* Natural language insights
* Recommended interventions
* Citizen advisories
* Administrative summaries

#### Storage Strategy

Generated responses are stored separately from raw environmental observations for auditing and future reference.

---

### 5.6 Simulated Datasets

#### Purpose

Certain datasets required by the problem statement are not publicly available in real time. During the MVP, UrbanSense uses realistic simulated datasets to demonstrate complete platform functionality.

#### Simulated Data

* Traffic Density
* Construction Activity
* Industrial Emissions
* Waste Burning Locations

#### Used By

* Pollution Source Attribution
* Recommendation Engine
* AI Analytics

#### Storage Strategy

Stored as static reference datasets in Supabase.

#### Future Replacement

Each simulated dataset is designed as a replaceable data provider and can later be connected to official government systems or IoT feeds without modifying the overall application architecture.

## 6. Data Integration Workflow

UrbanSense follows a centralized data integration architecture where all external data is collected, validated, normalized, and stored before being consumed by the frontend or AI services.

The frontend never communicates directly with external data providers. All integrations are handled by backend services to ensure security, caching, consistency, and future scalability.

---

### 6.1 Overall Data Flow

```text
External Data Sources
        │
        ▼
Data Collection Layer
        │
        ▼
Validation & Normalization
        │
        ▼
Supabase Database
        │
        ├──────────────┐
        ▼              ▼
FastAPI AI Services   REST APIs
        │              │
        └──────┬───────┘
               ▼
        React Frontend
               │
               ▼
Municipal Administrator
```

---

### 6.2 City Selection Workflow

UrbanSense supports multiple Indian cities through a searchable city selector available in the dashboard.

Workflow:

1. Administrator opens the dashboard.
2. Administrator searches for a city using the search bar.
3. Administrator selects a city from the suggestions.
4. The selected city becomes the active context for the session.
5. All widgets, maps, charts, forecasts, and recommendations refresh automatically using data for the selected city.
6. If ward-level data is available, the application displays hyperlocal analytics.
7. Otherwise, the application automatically falls back to city-level analytics.

No page reload is required during city switching.

---

### 6.3 Backend Data Ingestion Workflow

The backend is responsible for integrating all external datasets.

For every supported city, the backend:

1. Retrieves AQI observations.
2. Retrieves weather information.
3. Loads geospatial datasets.
4. Retrieves historical records.
5. Validates incoming data.
6. Normalizes different data formats into a common schema.
7. Stores raw observations in Supabase.
8. Triggers AI processing whenever new data becomes available.

---

### 6.4 Frontend Data Loading Workflow

When a city is selected, the frontend performs the following sequence:

1. Load dashboard statistics.
2. Load AQI observations.
3. Load monitoring stations.
4. Load weather information.
5. Load ward boundaries (if available).
6. Load charts and historical trends.
7. Load AI recommendations.
8. Render all components.

Each request is executed independently wherever possible to improve responsiveness.

---

### 6.5 AI Processing Workflow

The AI pipeline operates after environmental data has been collected.

Input:

* AQI observations
* Historical AQI
* Weather information
* Traffic density (simulated)
* Construction activity (simulated)
* Industrial zones
* Selected city

Processing:

* Feature engineering
* Pollution trend analysis
* AQI forecasting
* Pollution source attribution
* Recommendation generation
* Citizen advisory generation

Outputs:

* Forecasted AQI
* Confidence score
* Recommended interventions
* Citizen health advisories
* Administrative summaries

Generated AI outputs are stored separately from raw environmental observations to maintain traceability and enable future model improvements.

---

### 6.6 Design Principles

The data integration workflow follows these principles:

* External services are isolated behind backend integrations.
* All datasets are normalized before storage.
* Raw environmental data is never modified by AI processes.
* AI outputs remain explainable and traceable.
* The platform should continue functioning even when optional datasets are unavailable.
* Every workflow is designed to support additional Indian cities without architectural changes.

## 7. Data Refresh & Synchronization Strategy

UrbanSense integrates multiple categories of data sources, each with different update frequencies and synchronization requirements.

To optimize performance, reduce external API usage, and ensure a responsive user experience, the platform follows a hybrid refresh strategy combining scheduled synchronization, on-demand requests, and intelligent caching.

---

### 7.1 Data Categories

The platform classifies data into three categories:

#### Live Data

Frequently changing data retrieved from external providers.

Examples:

* AQI observations
* Weather information

---

#### Static Data

Rarely changing reference datasets.

Examples:

* Ward boundaries
* City boundaries
* Industrial zones
* Construction locations
* Sensitive infrastructure

---

#### AI Generated Data

Generated after processing environmental observations.

Examples:

* AQI forecasts
* Pollution source attribution
* AI recommendations
* Citizen advisories
* Administrative summaries

---

### 7.2 Refresh Schedule

| Data                 | Refresh Method                  | Frequency          |
| -------------------- | ------------------------------- | ------------------ |
| AQI Observations     | Scheduled Sync                  | Every 1 hour       |
| Weather Information  | Scheduled Sync                  | Every 1–3 hours    |
| Dashboard Statistics | On Demand                       | Every page refresh |
| AQI Forecast         | Triggered after new AQI data    | Hourly             |
| AI Recommendations   | Generated on demand             | User Request       |
| Citizen Advisories   | Generated after forecast update | Hourly             |
| Historical Trends    | Database Query                  | On Demand          |
| Ward Boundaries      | Manual Import                   | Rare               |
| Traffic Dataset      | Manual Update                   | As Needed          |
| Construction Dataset | Manual Update                   | As Needed          |

---

### 7.3 Synchronization Workflow

The synchronization process follows the sequence below:

```text
Scheduled Job
      │
      ▼
Fetch Latest AQI Data
      │
      ▼
Fetch Latest Weather Data
      │
      ▼
Validate & Normalize Data
      │
      ▼
Update Supabase Database
      │
      ▼
Run Forecasting Model
      │
      ▼
Generate AI Recommendations
      │
      ▼
Update Dashboard
```

---

### 7.4 Caching Strategy

To reduce unnecessary external requests, UrbanSense uses intelligent caching.

| Dataset            | Cache Duration  |
| ------------------ | --------------- |
| AQI Data           | 1 hour          |
| Weather Data       | 3 hours         |
| GeoJSON Files      | Until Updated   |
| Historical Data    | Permanent       |
| AI Recommendations | Current Session |

Cached data may continue to be displayed if external services are temporarily unavailable.

---

### 7.5 Synchronization Principles

The platform follows the following synchronization principles:

* Never request the same external data unnecessarily.
* Normalize all incoming data before storing it.
* Preserve historical environmental observations.
* Keep AI-generated insights separate from raw environmental data.
* Prefer cached data over failed API requests.
* Ensure all dashboard components display a consistent snapshot of data for the selected city.

---

### 7.6 Future Enhancements

The synchronization architecture is designed to support future improvements, including:

* Real-time streaming from IoT sensors
* Event-driven processing
* Message queues for scalable ingestion
* WebSocket-based live dashboard updates
* Automated data quality monitoring
* Incremental synchronization for large datasets

## 8. Data Storage Strategy

UrbanSense follows a layered storage architecture to ensure data integrity, scalability, and maintainability. Different categories of data are stored independently based on their purpose and lifecycle.

Supabase serves as the primary cloud database and storage provider for the application.

---

### 8.1 Storage Layers

The platform separates data into five logical layers:

#### Raw Environmental Data

Stores environmental observations exactly as received from external sources.

Examples:

* AQI observations
* Pollutant concentrations
* Weather information
* Monitoring station readings

Characteristics:

* Read-only after ingestion
* Never modified by AI services
* Used as the source of truth

---

#### Processed Analytics Data

Stores cleaned, normalized, and aggregated environmental information.

Examples:

* Daily AQI averages
* Weekly trends
* City statistics
* Ward-level summaries
* Pollution hotspot metrics

Characteristics:

* Generated from raw observations
* Optimized for dashboard queries
* Updated whenever new environmental data is synchronized

---

#### AI Generated Data

Stores outputs produced by AI services.

Examples:

* AQI forecasts
* Pollution source attribution
* Intervention recommendations
* Citizen advisories
* Administrative summaries
* Confidence scores

Characteristics:

* Generated on demand or after scheduled processing
* Stored independently from raw observations
* Traceable back to the source data used for generation

---

#### Reference Data

Stores datasets that change infrequently.

Examples:

* City metadata
* Ward boundaries
* GeoJSON files
* Industrial zones
* Construction sites
* Sensitive infrastructure

Characteristics:

* Updated manually or periodically
* Shared across multiple application modules
* Used to enrich analytics and geospatial visualizations

---

#### Application Data

Stores information required for application functionality.

Examples:

* User accounts
* User roles
* Dashboard preferences
* Saved reports
* System settings
* Audit logs

Characteristics:

* Managed by Supabase Authentication and the application backend
* Supports role-based access control
* Tracks administrative activity for auditing purposes

---

### 8.2 Storage Architecture

```text
                External Data Sources
                         │
                         ▼
                Raw Environmental Data
                         │
                         ▼
               Processed Analytics Data
                         │
                ┌────────┴────────┐
                ▼                 ▼
        AI Generated Data   Reference Data
                │                 │
                └────────┬────────┘
                         ▼
                  Application Layer
                         │
                         ▼
                 React Dashboard
```

---

### 8.3 Storage Principles

UrbanSense follows the following storage principles:

* Raw observations are immutable after ingestion.
* AI-generated insights are always stored separately from source data.
* Static datasets are imported once and reused across the platform.
* Historical records are preserved for trend analysis and forecasting.
* Every record is associated with its corresponding city.
* Ward-level information is stored only when available.
* The storage architecture must support onboarding new Indian cities without schema redesign.

---

### 8.4 Storage Technologies

| Data Category       | Storage Technology                     |
| ------------------- | -------------------------------------- |
| Environmental Data  | Supabase PostgreSQL                    |
| AI Outputs          | Supabase PostgreSQL                    |
| Reference Data      | Supabase PostgreSQL + Supabase Storage |
| GeoJSON Files       | Supabase Storage                       |
| Authentication      | Supabase Auth                          |
| Reports & Documents | Supabase Storage                       |
| Audit Logs          | Supabase PostgreSQL                    |

---

### 8.5 Future Storage Enhancements

The storage architecture has been designed to support future improvements, including:

* Time-series database optimization for high-frequency sensor data
* Geospatial indexing for faster map queries
* Automated archival of historical observations
* Multi-region database replication
* Distributed object storage for large geospatial datasets
* Data warehouse integration for long-term analytics

### 8.6 Geospatial Data Management

UrbanSense is a geospatial intelligence platform. To efficiently manage spatial information, the application uses the PostGIS extension available within Supabase PostgreSQL.

Rather than treating locations as simple latitude and longitude values, PostGIS enables the platform to store and query spatial objects such as points, lines, and polygons.

#### Spatial Data Managed

The platform stores and processes the following geospatial information:

* Cities
* Administrative boundaries
* Ward boundaries
* AQI monitoring stations
* Pollution hotspots
* Industrial zones
* Construction sites
* Hospitals
* Schools
* Other critical infrastructure

#### Why PostGIS?

Using PostGIS provides several advantages over traditional coordinate storage:

* Native geospatial data types
* Efficient spatial indexing
* Faster map-based queries
* Built-in geospatial functions
* Scalable support for large geographic datasets

These capabilities improve both application performance and future scalability.

#### Expected Geospatial Operations

UrbanSense will support operations such as:

* Display monitoring stations on the interactive map.
* Determine which ward contains a monitoring station.
* Display pollution hotspots within city or ward boundaries.
* Calculate distances between pollution sources and sensitive locations.
* Filter environmental data based on geographic regions.
* Generate heatmaps and spatial visualizations.

#### Future Capabilities

The chosen geospatial architecture allows future enhancements without redesigning the database, including:

* Radius-based environmental alerts
* Route pollution analysis
* Buffer zone calculations
* Satellite imagery overlays
* Live IoT sensor mapping
* Advanced geospatial analytics
> **Note:** During the MVP, only the geospatial capabilities required for the implemented features will be used. The remaining PostGIS capabilities are included to ensure the platform can scale as additional datasets and analytics are introduced.

## 9. Error Handling & Fallback Strategy

UrbanSense is designed to remain functional even when one or more external data sources become temporarily unavailable. The platform prioritizes graceful degradation over complete service interruption.

---

### 9.1 Error Handling Principles

The platform follows these principles:

* Never allow the failure of one data source to break the entire application.
* Display the latest cached data whenever possible.
* Clearly indicate when displayed information is not live.
* Log all integration failures for troubleshooting.
* Retry transient failures using controlled retry mechanisms.
* Separate external integration failures from application errors.

---

### 9.2 Fallback Strategy

| Data Source           | Failure Handling                                                     |
| --------------------- | -------------------------------------------------------------------- |
| CPCB Air Quality Data | Display latest cached observations                                   |
| Weather Data          | Use previous successful weather response                             |
| GeoJSON Boundaries    | Fall back to city-level visualization                                |
| Groq API              | Display rule-based recommendations instead of AI-generated responses |
| Historical Data       | Continue using stored historical records                             |
| Simulated Datasets    | Use existing static datasets                                         |

---

### 9.3 User Experience During Failures

If a data source becomes unavailable:

* Existing dashboard data should remain visible.
* Maps should continue functioning.
* Historical trends should remain accessible.
* AI modules should explain when recommendations are based on cached data.
* Users should never encounter blank dashboards because of a single integration failure.

---

### 9.4 Logging & Monitoring

The backend should maintain logs for:

* External API failures
* Invalid responses
* Synchronization failures
* Data validation errors
* AI processing failures

These logs assist debugging and future platform improvements.

## 10. Future Data Integrations

UrbanSense has been designed with an extensible integration architecture that allows additional data providers to be incorporated without significant architectural changes.

Potential future integrations include:

### Environmental Data

* Satellite imagery (Sentinel, MODIS)
* Real-time IoT air quality sensors
* Noise pollution sensors
* Water quality monitoring
* Meteorological department datasets

### Transportation

* Live traffic APIs
* Public transportation feeds
* Vehicle density datasets
* Fleet emission monitoring

### Government Systems

* Smart City Mission platforms
* Municipal GIS systems
* Pollution Control Board systems
* Construction permit databases
* Industrial emission registries

### Public Health

* Hospital occupancy
* Respiratory disease statistics
* Pharmacy demand trends
* Emergency response systems

### Citizen Engagement

* Mobile application feedback
* Citizen pollution reports
* Crowd-sourced environmental observations
* Public complaint management

### AI Enhancements

* Multi-model forecasting
* Satellite image analysis
* Computer vision for pollution detection
* Predictive intervention impact analysis
* Explainable AI dashboards

The modular architecture ensures these integrations can be added as independent providers without requiring changes to the frontend application.

## 11. Implementation Notes for Developers & AI Assistants

The following implementation guidelines should be followed throughout the development of UrbanSense.

### General Principles

* The frontend must never communicate directly with external APIs.
* All external integrations should be handled by backend services.
* Supabase serves as the primary cloud database and authentication provider.
* FastAPI is responsible for AI processing, forecasting, analytics, and custom business logic.
* Every dataset should be associated with a selected city.
* The application should support multiple Indian cities using the same architecture.

---

### Data Management

* Preserve raw environmental observations as immutable records.
* Store AI-generated outputs separately from source data.
* Normalize external datasets before persistence.
* Cache frequently accessed external responses whenever appropriate.
* Design all integrations as replaceable adapters.

---

### Geospatial Guidelines

* Use PostGIS for all spatial data.
* Store geographic features using native spatial types where applicable.
* Avoid manual distance calculations when PostGIS functions are available.
* Keep the geospatial layer independent of business logic.

---

### AI Guidelines

* AI services should consume normalized data only.
* Every AI recommendation should be explainable.
* Separate deterministic analytics from LLM-generated narratives.
* Allow future AI models to replace existing implementations without changing application workflows.

---

### Scalability Guidelines

The MVP focuses on demonstrating the complete workflow while maintaining an architecture capable of supporting:

* Additional Indian cities
* Additional environmental datasets
* Additional AI models
* Additional user roles
* Additional geospatial layers

Future expansion should require configuration and data onboarding rather than architectural redesign.
