import json
import random
from groq import Groq
from app.core.config import settings

def get_mock_ai_analysis(current_aqi: int, pollutants: dict) -> dict:
    """Fallback generator when Groq API is not configured or fails."""
    # Determine primary pollutant based on max value or simple mapping
    pm25 = pollutants.get("pm25", 0.0)
    pm10 = pollutants.get("pm10", 0.0)
    no2 = pollutants.get("no2", 0.0)
    co = pollutants.get("co", 0.0)
    so2 = pollutants.get("so2", 0.0)
    o3 = pollutants.get("o3", 0.0)

    # Simple rule-based source estimation
    total = pm25 + pm10 + no2 + (co * 100) + so2 + o3
    if total == 0:
        total = 1.0
        
    p_traffic = round((no2 + co * 50) / total * 100, 1)
    p_dust = round((pm10 * 0.7) / total * 100, 1)
    p_construction = round((pm10 * 0.3) / total * 100, 1)
    p_industrial = round((so2 * 1.5) / total * 100, 1)
    p_biomass = round((pm25 * 0.2) / total * 100, 1)

    # Normalize to 100
    subtotal = p_traffic + p_industrial + p_construction + p_dust + p_biomass
    if subtotal == 0:
        p_traffic = 35.0
        p_dust = 25.0
        p_construction = 20.0
        p_industrial = 15.0
        p_biomass = 5.0
    else:
        p_traffic = round(p_traffic / subtotal * 100, 1)
        p_industrial = round(p_industrial / subtotal * 100, 1)
        p_construction = round(p_construction / subtotal * 100, 1)
        p_dust = round(p_dust / subtotal * 100, 1)
        p_biomass = round(100.0 - (p_traffic + p_industrial + p_construction + p_dust), 1)

    # Choose primary
    primary = "PM2.5"
    max_val = pm25
    if pm10 > max_val:
        primary = "PM10"
        max_val = pm10
    if no2 > max_val:
        primary = "NO2"
        
    # Set risk levels
    if current_aqi <= 100:
        risk = "low"
        pop = "all"
        rec = "Air quality is satisfactory. No immediate municipal action required."
        steps = ["Maintain routine mechanical sweeping", "Monitor local residential construction projects"]
    elif current_aqi <= 200:
        risk = "moderate"
        pop = "sensitive_groups"
        rec = "Moderately poor air quality. Increase sweeping and enforce dust control regulations."
        steps = [
            "Increase mechanical sweeping frequency on key corridors",
            "Deploy anti-smog guns near high-activity construction zones",
            "Issue public warning for sensitive groups to limit prolonged outdoor exertion"
        ]
    else:
        risk = "high" if current_aqi <= 300 else "critical"
        pop = "all"
        rec = "Critical pollution levels detected. Deploy emergency misting cannons, halt unpaved road transport, and enforce construction bans."
        steps = [
            "Mandate immediate halt of non-essential construction and demolition",
            "Deploy city-wide anti-smog water sprinklers and misting cannons",
            "Divert heavy diesel vehicular traffic away from residential zones",
            "Activate smog towers at maximum capacity",
            "Issue emergency citizen health advisory advising N95 masks outdoors"
        ]

    return {
        "traffic": p_traffic,
        "industrial": p_industrial,
        "construction": p_construction,
        "road_dust": p_dust,
        "biomass_burning": p_biomass,
        "source_reasoning": f"Primary pollutant is {primary}. Higher levels of PM10 indicate heavy construction and road dust suspendables, while elevated CO levels indicate traffic emissions.",
        "primary_pollutant": primary,
        "recommendation_text": rec,
        "action_plan_steps": steps,
        "confidence_score": 0.82,
        "advisory_title": f"Air Quality Warning - {risk.capitalize()} Risk",
        "advisory_text": f"Current AQI is {current_aqi} ({risk.upper()}). Sensible precautions are recommended to protect respiratory health.",
        "advisory_risk_level": risk,
        "advisory_target_population": pop
    }


class GroqAIService:
    @staticmethod
    def analyze_air_quality(ward_name: str, current_aqi: int, pollutants: dict) -> dict:
        """
        Call Groq API using Llama 3.1 8B Instant in JSON mode to perform:
        1. Source attribution with reasoning.
        2. Action recommendations with concrete step action plans.
        3. Localized citizen advisory.
        """
        api_key = settings.GROQ_API_KEY
        if not api_key:
            print("[AI Service] Groq API Key not set. Using fallback rules.")
            return get_mock_ai_analysis(current_aqi, pollutants)
        
        try:
            client = Groq(api_key=api_key)
            
            prompt = f"""
            Analyze the following air quality metrics for the suburb/ward '{ward_name}':
            Current AQI: {current_aqi}
            Pollutants Breakdown: {json.dumps(pollutants)}
            
            Based on the pollutant relationships (e.g., high CO/NO2 implies vehicular traffic, high PM10 implies road dust/construction, high SO2/NO2 implies industrial activities):
            1. Estimate the percentage contributions from: traffic, industrial, construction, road_dust, and biomass_burning. They must sum to 100%.
            2. Write a detailed source attribution reasoning explanation.
            3. Generate administrative recommendation suggestions including a detailed step-by-step action plan for municipal authorities.
            4. Generate a localized public health advisory for citizens, assigning a risk level ('low', 'moderate', 'high', 'critical') and target population ('all', 'sensitive_groups').
            
            You must return a single JSON object matching this schema:
            {{
                "traffic": float,
                "industrial": float,
                "construction": float,
                "road_dust": float,
                "biomass_burning": float,
                "source_reasoning": string,
                "primary_pollutant": string,
                "recommendation_text": string,
                "action_plan_steps": [string],
                "confidence_score": float (between 0.0 and 1.0),
                "advisory_title": string,
                "advisory_text": string,
                "advisory_risk_level": string,
                "advisory_target_population": string
            }}
            """
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a senior environmental data scientist and smart city decision-support assistant. You always respond with a valid JSON object matching the requested schema."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1000
            )
            
            response_text = chat_completion.choices[0].message.content
            return json.loads(response_text)
            
        except Exception as e:
            print(f"[AI Service] Groq API call failed: {e}")
            return get_mock_ai_analysis(current_aqi, pollutants)
