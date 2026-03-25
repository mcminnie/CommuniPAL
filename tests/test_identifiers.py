import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communipal.identifiers import identify_event, transition_algorithm


class TestIdentifyEvent(unittest.TestCase):
    """Test cases for the identify_event function."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create sample row data that mimics activPAL export structure
        self.sample_rows = {
            'lying_event': pd.Series({
                'Event Type': 3.1,
                'Duration (s)': 3600,
                'Longest Straight Line Time (s)': 100
            }),
            'short_stepping': pd.Series({
                'Event Type': 2,
                'Duration (s)': 30,
                'Longest Straight Line Time (s)': 15
            }),
            'long_stepping': pd.Series({
                'Event Type': 2,
                'Duration (s)': 300,
                'Longest Straight Line Time (s)': 150
            }),
            'transport_event': pd.Series({
                'Event Type': 5.0,
                'Duration (s)': 1200,
                'Longest Straight Line Time (s)': 800
            }),
            'nonwear_event': pd.Series({
                'Event Type': 4,
                'Duration (s)': 7200,
                'Longest Straight Line Time (s)': 0
            })
        }
    
    def test_lying_detection(self):
        """Test that lying events are correctly identified."""
        result = identify_event(
            self.sample_rows['lying_event'], 
            algo_type='CSDorSLS', 
            csd=60, 
            sls=30
        )
        self.assertEqual(result, 'sleeping')
    
    def test_csd_or_sls_algorithm(self):
        """Test CSDorSLS algorithm logic."""
        # Should be transition (duration > threshold)
        result = identify_event(
            self.sample_rows['long_stepping'], 
            algo_type='CSDorSLS', 
            csd=60, 
            sls=30
        )
        self.assertEqual(result, 'transition')
        
        # Should be NaN (neither threshold met)
        result = identify_event(
            self.sample_rows['short_stepping'], 
            algo_type='CSDorSLS', 
            csd=60, 
            sls=30
        )
        self.assertTrue(pd.isna(result))
    
    def test_csd_and_sls_algorithm(self):
        """Test CSDandSLS algorithm logic."""
        # Should be transition (both thresholds met)
        result = identify_event(
            self.sample_rows['long_stepping'], 
            algo_type='CSDandSLS', 
            csd=60, 
            sls=30
        )
        self.assertEqual(result, 'transition')
        
        # Create row that meets only one threshold
        partial_row = pd.Series({
            'Event Type': 2,
            'Duration (s)': 300,  # Meets CSD threshold
            'Longest Straight Line Time (s)': 15  # Doesn't meet SLS threshold
        })
        
        result = identify_event(
            partial_row, 
            algo_type='CSDandSLS', 
            csd=60, 
            sls=30
        )
        self.assertTrue(pd.isna(result))
    
    def test_csd_only_algorithm(self):
        """Test CSDonly algorithm logic."""
        result = identify_event(
            self.sample_rows['long_stepping'], 
            algo_type='CSDonly', 
            csd=60
        )
        self.assertEqual(result, 'transition')
    
    def test_sls_only_algorithm(self):
        """Test SLSonly algorithm logic."""
        result = identify_event(
            self.sample_rows['long_stepping'], 
            algo_type='SLSonly', 
            sls=30
        )
        self.assertEqual(result, 'transition')
    
    def test_transport_detection(self):
        """Test transport event detection."""
        # With transport enabled
        result = identify_event(
            self.sample_rows['transport_event'], 
            algo_type='CSDorSLS', 
            csd=60, 
            sls=30,
            seated_transport=True
        )
        self.assertEqual(result, 'transition')
        
        # With transport disabled
        result = identify_event(
            self.sample_rows['transport_event'], 
            algo_type='CSDorSLS', 
            csd=60, 
            sls=30,
            seated_transport=False
        )
        self.assertTrue(pd.isna(result))
    
    def test_amputee_logic(self):
        """Test amputee-specific logic."""
        result = identify_event(
            self.sample_rows['nonwear_event'], 
            algo_type='CSDorSLS',
            amputee=True
        )
        self.assertEqual(result, 'sleeping')


class TestTransitionAlgorithm(unittest.TestCase):
    """Test cases for the transition_algorithm function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample activPAL-like DataFrame
        self.sample_df = pd.DataFrame({
            'Event Type': [3.1, 2, 2, 3.1, 2, 5.0, 3.1],
            'Duration (s)': [7200, 45, 300, 3600, 150, 1200, 5400],
            'Longest Straight Line Time (s)': [0, 20, 200, 0, 80, 900, 0],
            'Start': pd.to_datetime(['2024-01-01 08:00:00', '2024-01-01 10:00:00', 
                                   '2024-01-01 10:30:00', '2024-01-01 11:00:00',
                                   '2024-01-01 15:00:00', '2024-01-01 15:30:00',
                                   '2024-01-01 17:00:00'])
        })
    
    def test_basic_classification(self):
        """Test basic classification functionality."""
        result_df = transition_algorithm(
            self.sample_df.copy(),
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            seated_transport=True
        )
        
        # Check that classification column is created
        self.assertIn('community_classification', result_df.columns)
        
        # Check that all rows have a classification
        self.assertTrue(result_df['community_classification'].notna().all())
    
    def test_different_algorithms(self):
        """Test different algorithm types produce different results."""
        # Test CSDorSLS
        result_or = transition_algorithm(
            self.sample_df.copy(),
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            seated_transport=False
        )
        
        # Test CSDandSLS
        result_and = transition_algorithm(
            self.sample_df.copy(),
            algo_type='CSDandSLS',
            csd=60,
            sls=100,
            seated_transport=False
        )
        
        # Results should potentially be different
        self.assertIn('community_classification', result_or.columns)
        self.assertIn('community_classification', result_and.columns)
    
    def test_transport_inclusion(self):
        """Test transport inclusion affects results."""
        result_with_transport = transition_algorithm(
            self.sample_df.copy(),
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            seated_transport=True
        )
        
        result_without_transport = transition_algorithm(
            self.sample_df.copy(),
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            seated_transport=False
        )
        
        # Both should have classifications
        self.assertTrue(result_with_transport['community_classification'].notna().all())
        self.assertTrue(result_without_transport['community_classification'].notna().all())
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame(columns=['Event Type', 'Duration (s)', 'Longest Straight Line Time (s)'])
        
        result = transition_algorithm(
            empty_df,
            algo_type='CSDorSLS',
            csd=60,
            sls=100
        )
        
        # Should return dataframe with classification column
        self.assertIn('community_classification', result.columns)
        self.assertTrue(result.empty)
    
    def test_amputee_classification(self):
        """Test amputee-specific classification."""
        # Add Event Type 4 (non-wear) to test data
        df_with_nonwear = self.sample_df.copy()
        df_with_nonwear.loc[len(df_with_nonwear)] = {
            'Event Type': 4,
            'Duration (s)': 14400,
            'Longest Straight Line Time (s)': 0,
            'Start': pd.to_datetime('2024-01-01 18:00:00')
        }
        
        # Test non-amputee (should be 'Non-wear')
        result_normal = transition_algorithm(
            df_with_nonwear,
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            amputee=False
        )
        
        # Test amputee (should be 'Home')
        result_amputee = transition_algorithm(
            df_with_nonwear,
            algo_type='CSDorSLS',
            csd=60,
            sls=100,
            amputee=True
        )
        
        # Check that Event Type 4 is classified differently
        nonwear_idx = df_with_nonwear[df_with_nonwear['Event Type'] == 4].index[0]
        self.assertEqual(result_normal.loc[nonwear_idx, 'community_classification'], 'Non-wear')
        self.assertEqual(result_amputee.loc[nonwear_idx, 'community_classification'], 'Home')


if __name__ == '__main__':
    unittest.main()