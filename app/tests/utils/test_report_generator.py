import sys
from unittest.mock import MagicMock

# Define a mock early to ensure reportlab can be imported smoothly
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.colors'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.platypus'] = MagicMock()
sys.modules['reportlab.lib.styles'] = MagicMock()
sys.modules['reportlab.lib.units'] = MagicMock()
sys.modules['reportlab.lib.enums'] = MagicMock()

import pytest
from unittest.mock import MagicMock, patch

from app.utils.report_generator import GraphoReportGenerator

@pytest.fixture
def generator(tmp_path):
    # Use pytest's tmp_path fixture for isolated output directories
    return GraphoReportGenerator(output_dir=str(tmp_path))

def test_generate_basic_report_success(generator):
    with patch('app.utils.report_generator.SimpleDocTemplate') as mock_doc_template:
        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        analysis_data = {
            'overall_score': 85,
            'summary': 'A positive personality summary.',
            'traits': [
                {'trait': 'Confidence', 'score': 90, 'observation': 'High t-bar'},
                {'trait': 'Determination', 'score': 80, 'observation': 'Firm pressure'}
            ]
        }

        result = generator.generate_basic_report(
            submission_id="sub123",
            user_name="John Doe",
            analysis_data=analysis_data
        )

        assert "Grapho_Basic_sub123" in result
        assert result.endswith(".pdf")

        mock_doc_template.assert_called_once()
        mock_doc_instance.build.assert_called_once()
        args, kwargs = mock_doc_instance.build.call_args
        story = args[0]
        assert isinstance(story, list)
        assert len(story) > 0

def test_generate_basic_report_empty_data(generator):
    with patch('app.utils.report_generator.SimpleDocTemplate') as mock_doc_template:
        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        # Empty data gracefully handles defaults
        analysis_data = {}

        result = generator.generate_basic_report(
            submission_id="sub124",
            user_name="Jane Doe",
            analysis_data=analysis_data
        )

        assert "Grapho_Basic_sub124" in result
        mock_doc_instance.build.assert_called_once()

def test_generate_level3_health_report_success(generator):
    with patch('app.utils.report_generator.SimpleDocTemplate') as mock_doc_template:
        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        analysis_data = {
            'disclaimer_header': 'This is a test disclaimer.',
            'mind_body_link': {
                'psych_summary': 'Stress',
                'somatic_effect': 'Tension'
            },
            'vitality_audit': {
                'vitality_score': 75,
                'energy_pattern': 'Steady',
                'pressure_analysis': 'Normal'
            },
            'stress_map': {
                'tension_areas': ['Neck', 'Shoulders'],
                'analysis': 'Tension noted.'
            },
            'specific_indicators': [
                {'system': 'Digestive', 'observation': 'Uneven baseline', 'interpretation': 'Possible indigestion'}
            ],
            'graphotherapy_prescription': [
                {'issue': 'Anxiety', 'exercise': 'Loops', 'instruction': 'Draw loops', 'neuro_benefit': 'Calming'}
            ],
            'conclusion': 'Take care.'
        }

        result = generator.generate_level3_health_report(
            user_name="Alice",
            analysis_data=analysis_data
        )

        assert "Grapho_Advanced_Health" in result
        assert result.endswith(".pdf")

        mock_doc_template.assert_called_once()
        mock_doc_instance.build.assert_called_once()

def test_generate_level3_health_report_empty_data(generator):
    with patch('app.utils.report_generator.SimpleDocTemplate') as mock_doc_template:
        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        # Test with missing keys to ensure no KeyErrors occur
        analysis_data = {}

        result = generator.generate_level3_health_report(
            user_name="Bob",
            analysis_data=analysis_data
        )

        assert "Grapho_Advanced_Health" in result
        mock_doc_instance.build.assert_called_once()
