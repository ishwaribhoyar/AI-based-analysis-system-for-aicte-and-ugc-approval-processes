"""
Sample Data Generator for Forecasting Testing.
Generates realistic multi-year CSV data for testing forecasting features.
"""

import csv
import os
from typing import List, Dict
from datetime import datetime
import random


def generate_sample_faculty_csv(output_path: str, years: List[int] = None) -> str:
    """Generate sample faculty data CSV for multiple years."""
    if years is None:
        current_year = datetime.now().year
        years = list(range(current_year - 4, current_year + 1))
    
    data = []
    base_faculty = 50
    
    for year in years:
        # Gradual increase in faculty
        faculty_count = base_faculty + (year - years[0]) * 3 + random.randint(-2, 5)
        professors = max(5, int(faculty_count * 0.15))
        associate = max(10, int(faculty_count * 0.30))
        assistant = max(20, int(faculty_count * 0.50))
        phd_count = max(15, int(faculty_count * 0.40))
        
        data.append({
            'Year': year,
            'Academic Year': f"{year}-{str(year + 1)[-2:]}",
            'Total Faculty': faculty_count,
            'Professors': professors,
            'Associate Professors': associate,
            'Assistant Professors': assistant,
            'PhD Count': phd_count
        })
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return output_path


def generate_sample_student_csv(output_path: str, years: List[int] = None) -> str:
    """Generate sample student enrollment data CSV for multiple years."""
    if years is None:
        current_year = datetime.now().year
        years = list(range(current_year - 4, current_year + 1))
    
    data = []
    base_students = 500
    
    for year in years:
        # Gradual increase in enrollment
        total = base_students + (year - years[0]) * 50 + random.randint(-20, 30)
        male = int(total * 0.55)
        female = total - male
        intake = int(total * 0.20)
        
        data.append({
            'Year': year,
            'Academic Year': f"{year}-{str(year + 1)[-2:]}",
            'Total Students': total,
            'Male Students': male,
            'Female Students': female,
            'Annual Intake': intake
        })
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return output_path


def generate_sample_infrastructure_csv(output_path: str, years: List[int] = None) -> str:
    """Generate sample infrastructure data CSV for multiple years."""
    if years is None:
        current_year = datetime.now().year
        years = list(range(current_year - 4, current_year + 1))
    
    data = []
    base_area = 8000  # sqm
    
    for year in years:
        # Gradual improvement in infrastructure
        area = base_area + (year - years[0]) * 500 + random.randint(-200, 300)
        classrooms = 25 + (year - years[0]) * 2
        library = 600 + (year - years[0]) * 50
        labs = 12 + (year - years[0])
        computers = 200 + (year - years[0]) * 20
        
        data.append({
            'Year': year,
            'Academic Year': f"{year}-{str(year + 1)[-2:]}",
            'Built Up Area (sqm)': area,
            'Classrooms': classrooms,
            'Library Area (sqm)': library,
            'Total Labs': labs,
            'Computers': computers
        })
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return output_path


def generate_sample_placement_csv(output_path: str, years: List[int] = None) -> str:
    """Generate sample placement data CSV for multiple years."""
    if years is None:
        current_year = datetime.now().year
        years = list(range(current_year - 4, current_year + 1))
    
    data = []
    base_eligible = 400
    
    for year in years:
        # Improving placement rates
        eligible = base_eligible + (year - years[0]) * 30
        placed = int(eligible * (0.70 + (year - years[0]) * 0.03))  # 70% to 82%
        avg_salary = 350000 + (year - years[0]) * 25000
        highest = avg_salary * 2.5
        
        data.append({
            'Year': year,
            'Academic Year': f"{year}-{str(year + 1)[-2:]}",
            'Eligible Students': eligible,
            'Placed Students': placed,
            'Placement Rate (%)': round((placed / eligible) * 100, 2),
            'Average Package (INR)': avg_salary,
            'Highest Package (INR)': int(highest)
        })
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return output_path


def generate_all_sample_csvs(output_dir: str = "sample_data") -> Dict[str, str]:
    """Generate all sample CSV files for testing."""
    os.makedirs(output_dir, exist_ok=True)
    
    current_year = datetime.now().year
    years = list(range(current_year - 4, current_year + 1))
    
    files = {
        'faculty': generate_sample_faculty_csv(
            os.path.join(output_dir, 'sample_faculty_data.csv'),
            years
        ),
        'students': generate_sample_student_csv(
            os.path.join(output_dir, 'sample_student_data.csv'),
            years
        ),
        'infrastructure': generate_sample_infrastructure_csv(
            os.path.join(output_dir, 'sample_infrastructure_data.csv'),
            years
        ),
        'placement': generate_sample_placement_csv(
            os.path.join(output_dir, 'sample_placement_data.csv'),
            years
        )
    }
    
    return files


if __name__ == "__main__":
    # Generate sample data when run directly
    print("Generating sample CSV files for forecasting testing...")
    files = generate_all_sample_csvs()
    print(f"✅ Generated {len(files)} sample CSV files:")
    for name, path in files.items():
        print(f"  - {name}: {path}")

