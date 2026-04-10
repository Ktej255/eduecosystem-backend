import pytest
from unittest.mock import MagicMock, patch
import os

from app.utils.report_generator import GraphoReportGenerator

def test_init_creates_directory(tmp_path):
    output_dir = str(tmp_path / "reports")
    generator = GraphoReportGenerator(output_dir=output_dir)
    assert os.path.exists(output_dir)
    assert generator.output_dir == output_dir

@patch('app.utils.report_generator.SimpleDocTemplate')
def test_generate_basic_report(mock_doc_template, tmp_path):
    output_dir = str(tmp_path / "reports")
    generator = GraphoReportGenerator(output_dir=output_dir)

    mock_doc = MagicMock()
    mock_doc_template.return_value = mock_doc

    analysis_data = {
        'overall_score': 85,
        'summary': 'Great writing!',
        'traits': [
            {'trait': 'Confidence', 'score': 90, 'observation': 'Large signatures'}
        ]
    }

    result = generator.generate_basic_report(
        submission_id="12345",
        user_name="John Doe",
        analysis_data=analysis_data
    )

    # Assert
    # The actual code returns f"/{self.output_dir}/{filename}" which adds an extra leading slash
    assert result.startswith(f"/{output_dir}/Grapho_Basic_12345_")
    assert result.endswith(".pdf")

    # Assert build was called
    mock_doc.build.assert_called_once()

    # Ensure story is passed to build
    args, kwargs = mock_doc.build.call_args
    story = args[0]
    assert isinstance(story, list)
    assert len(story) > 0

@patch('app.utils.report_generator.SimpleDocTemplate')
def test_generate_level3_health_report(mock_doc_template, tmp_path):
    output_dir = str(tmp_path / "reports")
    generator = GraphoReportGenerator(output_dir=output_dir)

    mock_doc = MagicMock()
    mock_doc_template.return_value = mock_doc

    analysis_data = {
        'disclaimer_header': 'Test Disclaimer',
        'mind_body_link': {
            'psych_summary': 'Psych summary',
            'somatic_effect': 'Somatic effect'
        },
        'vitality_audit': {
            'vitality_score': 80,
            'energy_pattern': 'Steady',
            'pressure_analysis': 'Even pressure'
        },
        'stress_map': {
            'tension_areas': ['Neck', 'Shoulders'],
            'analysis': 'High stress'
        },
        'specific_indicators': [
            {
                'system': 'Nervous',
                'observation': 'Shaky lines',
                'interpretation': 'Anxiety'
            }
        ],
        'graphotherapy_prescription': [
            {
                'issue': 'Anxiety',
                'exercise': 'Garland',
                'instruction': 'Draw loops',
                'neuro_benefit': 'Calms mind'
            }
        ],
        'conclusion': 'Take care.'
    }

    result = generator.generate_level3_health_report(
        user_name="Jane Doe",
        analysis_data=analysis_data
    )

    # Assert
    # The code hardcodes /uploads/reports/ for level3 reports
    assert result.startswith(f"/uploads/reports/Grapho_Advanced_Health_")
    assert result.endswith(".pdf")

    # Assert build was called
    mock_doc.build.assert_called_once()

    # Ensure story is passed to build
    args, kwargs = mock_doc.build.call_args
    story = args[0]
    assert isinstance(story, list)
    assert len(story) > 0
