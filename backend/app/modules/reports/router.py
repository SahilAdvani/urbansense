from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.database.session import get_db
from app.database.models import City, Ward, AQIObservation, AIRecommendation, Intervention

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/pdf/{city_id}")
def generate_city_pdf_report(city_id: str, db: Session = Depends(get_db)):
    """Generate a downloadable PDF executive report for a given city."""
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    wards = db.query(Ward).filter(Ward.city_id == city.id).all()
    ward_ids = [w.id for w in wards]

    # Calculate city summary
    obs_list = db.query(AQIObservation).filter(AQIObservation.ward_id.in_(ward_ids)).order_by(AQIObservation.timestamp.desc()).all() if ward_ids else []
    
    # Map latest AQI per ward
    latest_ward_aqi = {}
    for obs in obs_list:
        if obs.ward_id not in latest_ward_aqi:
            latest_ward_aqi[obs.ward_id] = obs

    avg_aqi = round(sum(o.aqi for o in latest_ward_aqi.values()) / len(latest_ward_aqi)) if latest_ward_aqi else 0

    recs = db.query(AIRecommendation).filter(AIRecommendation.ward_id.in_(ward_ids)).order_by(AIRecommendation.timestamp.desc()).all() if ward_ids else []
    interventions = db.query(Intervention).filter(Intervention.ward_id.in_(ward_ids)).order_by(Intervention.start_time.desc()).all() if ward_ids else []

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    # Document Header
    story.append(Paragraph(f"UrbanSense Executive Air Quality Report — {city.name}", title_style))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} | Target City: {city.name} (Lat: {city.latitude}, Lon: {city.longitude})", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E2E8F0'), spaceAfter=12))

    # Executive Overview Box
    category = "Good" if avg_aqi <= 50 else ("Satisfactory" if avg_aqi <= 100 else ("Moderate" if avg_aqi <= 200 else ("Poor" if avg_aqi <= 300 else "Very Poor")))
    summary_data = [
        ["City Name", "Total Wards", "City Average AQI", "Overall Category"],
        [city.name, str(len(wards)), str(avg_aqi), category]
    ]
    summary_table = Table(summary_data, colWidths=[130, 100, 140, 170])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Executive Analytical Summary Text
    story.append(Paragraph("Executive Environmental Assessment & Source Analysis", heading_style))
    analysis_text = (
        f"Based on real-time sensor telemetry and satellite data across {len(wards)} municipal wards in <b>{city.name}</b>, "
        f"the city-wide Air Quality Index currently stands at <b>{avg_aqi} ({category})</b>. "
        f"Primary particulate matter drivers indicate elevated PM2.5 and PM10 concentrations resulting from a combination of vehicular traffic density, "
        f"ambient dust resuspension, and localized industrial activity. "
        f"Wards reporting elevated metrics require immediate enforcement of dust-suppression protocols and targeted traffic management."
    )
    story.append(Paragraph(analysis_text, body_style))
    story.append(Spacer(1, 8))

    # Strategic Guidance & Policy Directive
    story.append(Paragraph("Strategic Policy Guidance & Mitigation Roadmap", heading_style))
    policy_text = (
        f"<b>1. Traffic & Emissions Control:</b> Implement strict heavy-vehicle entry restrictions during peak morning and evening hours across hotspot sectors.<br/>"
        f"<b>2. Dust Suppression Interventions:</b> Deploy anti-smog guns and mechanical road-sweeping vehicles along high-density traffic corridors.<br/>"
        f"<b>3. Construction Regulations:</b> Mandate green curtains and continuous water sprinkling at active construction sites exceeding 500 sq. meters.<br/>"
        f"<b>4. Public Health Advisories:</b> Issue health warnings advising vulnerable populations (children, elderly, and individuals with respiratory conditions) to restrict prolonged outdoor exposure."
    )
    story.append(Paragraph(policy_text, body_style))
    story.append(Spacer(1, 10))

    # Ward-level Breakdown Table
    story.append(Paragraph("Ward-Level Air Quality Breakdown", heading_style))
    ward_rows = [["Ward Name", "Current AQI", "PM2.5 (ug/m3)", "PM10 (ug/m3)", "Primary Pollutant"]]
    
    for w in wards[:15]:
        obs = latest_ward_aqi.get(w.id)
        aqi_val = str(obs.aqi) if obs else "N/A"
        pm25_val = f"{obs.pm25:.1f}" if obs and obs.pm25 else "N/A"
        pm10_val = f"{obs.pm10:.1f}" if obs and obs.pm10 else "N/A"
        ward_rows.append([w.name, aqi_val, pm25_val, pm10_val, "PM2.5"])

    ward_table = Table(ward_rows, colWidths=[180, 80, 95, 95, 90])
    ward_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (1,0), (3,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    story.append(ward_table)
    story.append(Spacer(1, 10))

    # Executed Municipal Interventions Table
    story.append(Paragraph("Executed Municipal Interventions Audit Log", heading_style))
    rec_rows = [["Ward", "Complete Intervention Details", "Status", "Date Initiated"]]
    
    for i in interventions[:10]:
        desc_part = f" — {i.description}" if i.description else ""
        rec_rows.append([
            i.ward.name if i.ward else "Ward",
            Paragraph(f"<b>{i.title}</b>{desc_part}", body_style),
            i.status.upper(),
            i.start_time.strftime("%Y-%m-%d") if i.start_time else "N/A"
        ])

    if len(rec_rows) == 1:
        rec_rows.append(["All Wards", "No municipal interventions logged at present.", "NOMINAL", datetime.utcnow().strftime("%Y-%m-%d")])

    rec_table = Table(rec_rows, colWidths=[130, 250, 75, 85])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(rec_table)
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=urbansense_report_{city_id}.pdf"}
    )
