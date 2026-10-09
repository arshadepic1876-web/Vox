import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.task_parser import task_parser_service

examples = [
    "Complete my DBMS assignment tomorrow at 4 PM.",
    "Call Rahul at 6 PM today.",
    "Buy groceries this evening.",
    "Submit project report on Friday. Make it high priority.",
    "Study operating systems for two hours tomorrow.",
    "Urgently finish the presentation before 10 AM.",
]

print("=" * 60)
print("VERIFYING TASK PARSER ON REAL SPOKEN EXAMPLES:")
print("=" * 60)

for ex in examples:
    parsed = task_parser_service.parse_transcription(ex)
    print(f"INPUT: \"{ex}\"")
    print(f"  Title:    {parsed['title']}")
    print(f"  Date:     {parsed['due_date']}")
    print(f"  Time:     {parsed['due_time']}")
    print(f"  Priority: {parsed['priority']}")
    print(f"  Urgent:   {parsed['urgent']}")
    print(f"  Category: {parsed['category']}")
    print(f"  Duration: {parsed['estimated_duration_minutes']} min")
    print("-" * 60)
