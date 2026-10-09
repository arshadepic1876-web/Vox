import sys
from pathlib import Path
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.task_parser import task_parser_service

multilingual_samples = [
    # Hindi (Devanagari)
    "कल शाम 5 बजे मुझे पाइथन असाइनमेंट जमा करना है बहुत जरूरी है",
    # Hinglish (Hindi in Roman script)
    "Kal shaam 5 baje Python assignment submit karna hai bohot urgent hai",
    # Spanish
    "Entregar la tarea de Python mañana a las 5 PM. Es muy importante.",
    # French
    "Soumettre le devoir de Python demain à 17h. C'est très important.",
    # German
    "Python Aufgabe morgen um 17 Uhr einreichen. Sehr wichtig.",
    # English
    "Remind me to submit my Python assignment tomorrow at 5 PM. It is very important.",
]

print("=" * 65)
print("TESTING MULTILINGUAL SPEECH UNDERSTANDING:")
print("=" * 65)

for s in multilingual_samples:
    out = task_parser_service.parse_transcription(s)
    print(f"INPUT: \"{s}\"")
    print(f"  Detected Lang: {out.get('detected_language')}")
    print(f"  Title:         {out['title']}")
    print(f"  Due Date:      {out['due_date']}")
    print(f"  Due Time:      {out['due_time']}")
    print(f"  Priority:      {out['priority']}")
    print(f"  Urgent:        {out['urgent']}")
    print(f"  Category:      {out['category']}")
    print("-" * 65)
