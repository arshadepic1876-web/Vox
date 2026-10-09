import re
import json
import logging
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
from config.settings import Config
from utils.validation import validate_task_payload

logger = logging.getLogger(__name__)


class TaskParserService:
    """
    Intelligent Task Understanding Engine.
    Transforms natural spoken English into structured task attributes.
    Supports both LLM (Bedrock / OpenAI) and high-accuracy offline rule-based NLP.
    """

    def __init__(self):
        self.timezone_name = Config.TIMEZONE

    def parse_transcription(self, text: str) -> Dict[str, Any]:
        """
        Main entry point for task parsing.
        """
        if not text or not text.strip():
            return {
                "title": "New Voice Task",
                "description": "",
                "due_date": None,
                "due_time": None,
                "priority": "MEDIUM",
                "urgent": False,
                "category": "Other",
                "status": "pending",
                "estimated_duration_minutes": None,
                "raw_transcription": "",
            }

        text = text.strip()
        logger.info("Parsing task intent from transcription: '%s'", text)

        # Determine reference datetime in the configured timezone
        try:
            tz = ZoneInfo(self.timezone_name)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()

        # Try LLM provider if configured
        if Config.AI_PARSER_PROVIDER in ("openai", "bedrock") and Config.OPENAI_API_KEY:
            try:
                candidate = self._parse_with_openai(text, now)
                return validate_task_payload(candidate)
            except Exception as e:
                logger.warning("LLM parser failed, falling back to rule-based NLP: %s", e)

        # Use deterministic rule-based NLP engine
        candidate = self._parse_rule_based(text, now)
        return validate_task_payload(candidate)

    def _parse_rule_based(self, text: str, now: datetime) -> Dict[str, Any]:
        """
        Deterministic NLP extractor using regex, temporal resolution, and intent matching.
        Runs 100% offline with zero external API fees.
        """
        lower_text = text.lower()
        detected_lang = self._detect_language(text, lower_text)

        # 1. URGENCY EXTRACTION (Multilingual: English, Hindi/Hinglish, Spanish, French, German)
        urgent = bool(
            re.search(
                r"\b(urgent|urgently|asap|immediately|right away|emergency|without delay|"
                r"jaldi|turant|zaroori|bohot zaroori|bahut zaroori|तुरंत|जल्दी|"
                r"urgente|de inmediato|urgemment|immédiatement|dringend|sofort)\b",
                lower_text,
            )
        )

        # 2. PRIORITY EXTRACTION (Multilingual)
        priority = "MEDIUM"
        if re.search(
            r"\b(critical|emergency|blocker|highest priority|bohot zaroori|bahut zaroori|बहुत जरूरी|"
            r"crítico|critique|kritisch|höchste priorität)\b",
            lower_text,
        ):
            priority = "CRITICAL"
        elif re.search(
            r"\b(very important|important|high priority|crucial|vital|zaroori|khas|जरूरी|"
            r"muy importante|importante|très important|sehr wichtig|wichtig)\b",
            lower_text,
        ):
            priority = "HIGH"
        elif re.search(
            r"\b(low priority|not important|whenever|minor|not urgent|kam zaroori|कम जरूरी|"
            r"poco importante|pas important|nicht wichtig)\b",
            lower_text,
        ):
            priority = "LOW"

        # 3. CATEGORY EXTRACTION (Multilingual)
        category = "Other"
        category_keywords = {
            "College": [
                # English
                "assignment", "homework", "exam", "college", "university", "professor",
                "class", "syllabus", "lecture", "campus", "dbms", "os", "algorithm",
                "lab", "semester", "submission", "quiz", "faculty",
                # Hindi / Hinglish
                "असाइनमेंट", "परीक्षा", "कॉलेज", "पढ़ाई", "padhai", "dakhila", "kaksha",
                # Spanish, French, German
                "tarea", "examen", "universidad", "devoir", "cours", "hausaufgabe", "prüfung"
            ],
            "Work": [
                # English
                "work", "office", "client", "boss", "manager", "project report",
                "presentation", "deck", "contract", "salary", "jira", "ticket",
                # Hindi / Hinglish
                "काम", "ऑफिस", "नौकरी", "kam", "kaam", "naukri",
                # Spanish, French, German
                "trabajo", "oficina", "informe", "travail", "bureau", "arbeit", "büro", "projekt"
            ],
            "Meeting": [
                # English
                "meeting", "call", "sync", "standup", "zoom", "meet", "discuss with",
                "conference", "interview",
                # Hindi / Hinglish
                "मीटिंग", "कॉल", "बात करनी", "milna", "baat karni",
                # Spanish, French, German
                "reunión", "llamar", "llamada", "rendez-vous", "appeler", "treffen", "anrufen"
            ],
            "Study": [
                "study", "read chapter", "prepare", "revision", "learn", "course",
                "tutorial", "read book", "padhna", "padhai", "estudiar", "étudier", "lernen"
            ],
            "Shopping": [
                # English
                "buy", "groceries", "purchase", "order", "store", "market", "milk", "vegetables",
                # Hindi / Hinglish
                "सब्जी", "खरीदना", "दुकान", "sabzi", "sabji", "khareedna", "kharidna", "doodh",
                # Spanish, French, German
                "comprar", "compras", "supermercado", "acheter", "courses", "kaufen", "einkaufen"
            ],
            "Health": [
                "doctor", "medicine", "pill", "workout", "gym", "dentist", "hospital",
                "clinic", "exercise", "walk", "डॉक्टर", "दवा", "dawa", "dawai",
                "médico", "medicina", "médecin", "santé", "arzt", "medizin"
            ],
            "Finance": [
                "bill", "pay", "rent", "fee", "fees", "bank", "invoice", "emi", "tax", "transfer",
                "बिल", "किराया", "फीस", "kiraya", "paisa", "factura", "pagar", "payer", "zahlen"
            ],
            "Personal": [
                "call mom", "call dad", "family", "dinner", "friend", "birthday", "party", "clean room",
                "घर", "दोस्त", "dost", "ghar", "familia", "amigo", "famille", "ami", "familie"
            ],
        }

        for cat, keywords in category_keywords.items():
            pattern = r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
            if re.search(pattern, lower_text):
                category = cat
                break

        # 4. DURATION EXTRACTION (e.g., "for 2 hours", "do ghante", "2 horas")
        estimated_duration = None
        duration_hour_match = re.search(
            r"\b(?:for\s+)?(\d+|one|two|three|four|five|ek|do|teen|char|paanch)\s*(?:hours?|ghante|घंटे|horas?|heures?|stunden?)\b",
            lower_text,
        )
        word_numbers = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
            "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5,
        }
        if duration_hour_match:
            val = duration_hour_match.group(1)
            hours = word_numbers.get(val, int(val) if val.isdigit() else 1)
            estimated_duration = hours * 60
        else:
            duration_min_match = re.search(
                r"\b(?:for\s+)?(\d+)\s*(?:minutes?|min|मिनट|minutos?)\b",
                lower_text,
            )
            if duration_min_match:
                estimated_duration = int(duration_min_match.group(1))

        # 5. DUE DATE & DUE TIME EXTRACTION (Multilingual)
        due_date = None
        due_time = None

        # Resolve Relative Dates
        # Day after tomorrow: "day after tomorrow", "parso", "परसों", "pasado mañana", "après-demain", "übermorgen"
        if re.search(r"\b(day after tomorrow|parso|parson|परसों|pasado mañana|après-demain|übermorgen)\b", lower_text):
            target_date = now.date() + timedelta(days=2)
            due_date = target_date.strftime("%Y-%m-%d")
        # Tomorrow: "tomorrow", "kal", "कल", "mañana", "demain", "morgen"
        elif re.search(r"\b(tomorrow|kal|कल|mañana|demain|morgen)\b", lower_text):
            target_date = now.date() + timedelta(days=1)
            due_date = target_date.strftime("%Y-%m-%d")
        # Today: "today", "tonight", "this evening", "aaj", "आज", "hoy", "ce soir", "aujourd'hui", "heute"
        elif re.search(r"\b(today|tonight|this evening|aaj|आज|hoy|esta noche|aujourd'hui|ce soir|heute)\b", lower_text):
            due_date = now.date().strftime("%Y-%m-%d")
        else:
            # Check for weekday mentions (English, Hindi, Spanish, French, German)
            weekdays = {
                "monday": 0, "somwar": 0, "सोमवार": 0, "lunes": 0, "lundi": 0, "montag": 0,
                "tuesday": 1, "mangalwar": 1, "मंगलवार": 1, "martes": 1, "mardi": 1, "dienstag": 1,
                "wednesday": 2, "budhwar": 2, "बुधवार": 2, "miércoles": 2, "mercredi": 2, "mittwoch": 2,
                "thursday": 3, "guruwar": 3, "गुरुवार": 3, "jueves": 3, "jeudi": 3, "donnerstag": 3,
                "friday": 4, "shukrawar": 4, "शुक्रवार": 4, "viernes": 4, "vendredi": 4, "freitag": 4,
                "saturday": 5, "shaniwar": 5, "शनिवार": 5, "sábado": 5, "samedi": 5, "samstag": 5,
                "sunday": 6, "raviwar": 6, "रविवार": 6, "domingo": 6, "dimanche": 6, "sonntag": 6,
            }
            for day_name, day_idx in weekdays.items():
                if re.search(rf"\b(on|this|next|ko|को)?\s*{day_name}\b", lower_text):
                    current_idx = now.weekday()
                    days_ahead = (day_idx - current_idx) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target_date = now.date() + timedelta(days=days_ahead)
                    due_date = target_date.strftime("%Y-%m-%d")
                    break

        # Resolve Time (e.g., "5 PM", "at 4 PM", "shaam 5 baje", "4 baje", "५ बजे", "a las 5", "à 17h")
        time_match = re.search(r"\b(?:at|before|by|ko|को|a las|à|um)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje|बजे|h|uhr)?\b", lower_text)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = (time_match.group(3) or "").lower()

            # Check if evening / night context implies PM
            is_evening_context = bool(re.search(r"\b(shaam|sham|शाम|raat|रात|evening|tonight|noche|soir|abend)\b", lower_text))
            is_morning_context = bool(re.search(r"\b(subah|सुबह|morning|mañana|matin|morgen)\b", lower_text))

            if (meridiem == "pm" or (is_evening_context and not meridiem == "am")) and hours < 12:
                hours += 12
            elif (meridiem == "am" or is_morning_context) and hours == 12:
                hours = 0
            
            if 0 <= hours <= 23:
                due_time = f"{hours:02d}:{minutes:02d}"

        if not due_time:
            if re.search(r"\b(shaam|sham|शाम|this evening|in the evening|ce soir|esta tarde)\b", lower_text):
                due_time = "18:00"
            elif re.search(r"\b(tonight|raat|रात|esta noche)\b", lower_text):
                due_time = "20:00"
            elif re.search(r"\b(subah|सुबह|in the morning|matin)\b", lower_text):
                due_time = "09:00"
            elif re.search(r"\b(dophar|दोपहर|afternoon|après-midi)\b", lower_text):
                due_time = "14:00"
            else:
                due_time = "17:00"

        # If user did not mention any date, default to tomorrow so date picker is pre-populated
        if not due_date:
            due_date = (now.date() + timedelta(days=1)).strftime("%Y-%m-%d")

        # 6. TITLE EXTRACTION & CLEANING
        cleaned_title = text
        # Strip conversational prefix fillers (English, Hindi, Spanish, French, German)
        cleaned_title = re.sub(
            r"^(remind me to|i need to|i have to|please remind me to|please|make sure to|"
            r"schedule a task to|create a task to|can you remind me to|"
            r"mujhe|hume|kripya|recordarme|por favor|rappel-moi|rappelle-moi|erinnere mich daran)\s+",
            "",
            cleaned_title,
            flags=re.IGNORECASE,
        ).strip()

        # Remove trailing priority/urgency sentences
        cleaned_title = re.sub(
            r"\s*(?:it is|make it|this is|yeh|ye|es|c'est)?\s*"
            r"(?:very\s+important|high\s+priority|important|urgent|asap|critical|"
            r"bohot\s+zaroori|bahut\s+zaroori|zaroori\s+hai|turant|jaldi|"
            r"बहुत\s+जरूरी|जरूरी\s+है|muy\s+importante|urgente|très\s+important|sehr\s+wichtig)\.?\s*$",
            "",
            cleaned_title,
            flags=re.IGNORECASE,
        ).strip()

        # Remove explicit time/date suffixes from title
        cleaned_title = re.sub(
            r"\b(?:tomorrow|today|tonight|this evening|day after tomorrow|"
            r"kal|aaj|parso|shaam|subah|कल|आज|परसों|mañana|hoy|demain|morgen)\b\s*"
            r"(?:at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|baje)?)?",
            " ",
            cleaned_title,
            flags=re.IGNORECASE,
        )
        cleaned_title = re.sub(r"\s*[\.,;:!\?]+\s*$", "", cleaned_title).strip()
        cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()
        if not cleaned_title or len(cleaned_title) < 3:
            cleaned_title = text.strip()

        cleaned_title = cleaned_title[0].upper() + cleaned_title[1:] if cleaned_title else "New Task"

        return {
            "title": cleaned_title,
            "description": text.strip(),
            "due_date": due_date,
            "due_time": due_time,
            "priority": priority,
            "urgent": urgent,
            "category": category,
            "status": "pending",
            "estimated_duration_minutes": estimated_duration,
            "raw_transcription": text.strip(),
            "detected_language": detected_lang,
        }

    def _detect_language(self, text: str, lower_text: str) -> str:
        """Helper to detect language from script and distinctive keywords."""
        # Devanagari script (Hindi, Marathi, Nepali)
        if re.search(r"[\u0900-\u097F]", text):
            return "Hindi (हिंदी)"

        # Hinglish indicators
        if re.search(r"\b(kal|aaj|parso|shaam|subah|dophar|raat|karna|karne|karni|karo|hai|hain|baje|zaroori|sabji|sabzi|padhai|mujhe|hume)\b", lower_text):
            return "Hinglish (Hindi-English)"

        # Spanish indicators (distinctive words)
        if re.search(r"\b(mañana|hoy|tarea|llamar|reunión|hacer|semana|por favor|muy importante|a las)\b", lower_text):
            return "Spanish (Español)"

        # French indicators (distinctive words)
        if re.search(r"\b(demain|aujourd'hui|devoir|réunion|faire|très important|s'il vous plaît|rappelle-moi|c'est)\b", lower_text):
            return "French (Français)"

        # German indicators (distinctive words)
        if re.search(r"\b(morgen|heute|aufgabe|wichtig|dringend|machen|bitte|sehr wichtig)\b", lower_text):
            return "German (Deutsch)"

        return "English"


    def _parse_with_openai(self, text: str, now: datetime) -> Dict[str, Any]:
        """Optional OpenAI / Bedrock LLM structured output parser."""
        import requests

        prompt = (
            f"You are an AI task extraction assistant. Extract structured task data from this spoken text:\n"
            f"Text: \"{text}\"\n"
            f"Reference Current Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')} (Timezone: {self.timezone_name})\n"
            f"Return JSON strictly adhering to schema:\n"
            f"{{\n"
            f'  "title": string,\n'
            f'  "description": string,\n'
            f'  "due_date": "YYYY-MM-DD" or null,\n'
            f'  "due_time": "HH:MM" (24h) or null,\n'
            f'  "priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            f'  "urgent": boolean,\n'
            f'  "category": "College" | "Work" | "Personal" | "Shopping" | "Health" | "Finance" | "Meeting" | "Study" | "Other",\n'
            f'  "estimated_duration_minutes": integer or null\n'
            f"}}"
        )

        headers = {
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You output strictly valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
        res.raise_for_status()
        out = res.json()["choices"][0]["message"]["content"]
        data = json.loads(out)
        data["raw_transcription"] = text
        return data


# Singleton instance
task_parser_service = TaskParserService()
