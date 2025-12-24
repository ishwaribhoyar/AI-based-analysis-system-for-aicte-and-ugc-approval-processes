"""Debug Infrastructure Score calculation with detailed output."""
import sys
from pathlib import Path
import math
sys.path.insert(0, str(Path(__file__).parent))

from utils.parse_numeric import parse_numeric

# Full sample PDF expected data
sample_data = {
    "built_up_area_sqm": 18500,
    "built_up_area_sqm_num": 18500,
    "total_students": 1290,
    "total_students_num": 1290,
    "classrooms": 42,
    "tutorial_rooms": 16,
    "library_area_sqm": 750,
    "library_seating": 120,
    "digital_library_systems": True,
    "hostel_capacity": 0,  # Not in sample PDF
}

student_count = sample_data["total_students_num"]
print(f"Student count: {student_count}")

# 1. Area Score (40% weight)
built_up_area_sqm = sample_data["built_up_area_sqm_num"]
required_area = student_count * 4
area_score = min(100.0, (built_up_area_sqm / required_area) * 100) if required_area > 0 else 0.0
normalized_area = area_score / 100.0
print(f"Area: {built_up_area_sqm} sqm, Required: {required_area} sqm")
print(f"Area Score (raw): {area_score:.2f}% -> normalized: {normalized_area:.2f}")

# 2. Classroom Score (25% weight)
actual_classrooms = sample_data["classrooms"]
required_classrooms = math.ceil(student_count / 40)
classroom_score = min(1.0, actual_classrooms / required_classrooms) if required_classrooms > 0 else 0.0
print(f"Classrooms: {actual_classrooms}, Required: {required_classrooms}")
print(f"Classroom Score: {classroom_score:.2f}")

# 3. Library Score (15% weight)
library_area_sqm = sample_data["library_area_sqm"]
required_library = student_count * 0.5
library_score = min(1.0, library_area_sqm / required_library) if required_library > 0 else 0.0
print(f"Library Area: {library_area_sqm} sqm, Required: {required_library} sqm")
print(f"Library Score: {library_score:.2f}")

# 4. Digital Library Score (10% weight)
digital_resources = 0  # Not numeric in sample PDF
digital_library_score = min(1.0, digital_resources / 500)
print(f"Digital Resources: {digital_resources}, Target: 500")
print(f"Digital Library Score: {digital_library_score:.2f}")

# 5. Hostel Score (10% weight)
hostel_capacity = sample_data["hostel_capacity"]
required_hostel = student_count * 0.4
hostel_score = min(1.0, hostel_capacity / required_hostel) if required_hostel > 0 else 0.0
print(f"Hostel Capacity: {hostel_capacity}, Required: {required_hostel}")
print(f"Hostel Score: {hostel_score:.2f}")

# Weighted infrastructure score
infra_score = 100 * (
    0.40 * normalized_area +
    0.25 * classroom_score +
    0.15 * library_score +
    0.10 * digital_library_score +
    0.10 * hostel_score
)
print()
print(f"Weighted Calculation:")
print(f"  40% * {normalized_area:.2f} = {0.40 * normalized_area:.2f}")
print(f"  25% * {classroom_score:.2f} = {0.25 * classroom_score:.2f}")
print(f"  15% * {library_score:.2f} = {0.15 * library_score:.2f}")
print(f"  10% * {digital_library_score:.2f} = {0.10 * digital_library_score:.2f}")
print(f"  10% * {hostel_score:.2f} = {0.10 * hostel_score:.2f}")
print(f"  Total = {infra_score:.2f}")
print()
print(f"ACTUAL INFRASTRUCTURE SCORE: {infra_score:.2f}")
print(f"EXPECTED: 14.34")
print()

# Alternative formula that produces 14.34
alt_score = (required_area / built_up_area_sqm) * 51.38
print(f"Alternative formula (required/actual * 51.38): {alt_score:.2f}")
