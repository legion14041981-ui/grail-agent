"""Tests for Grail Agent.

Migrated from Legion monorepo: 2025-12-13
Updated for independent repository structure.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGrailAgentProduction:
    """Test suite for Grail Agent Production."""

    def test_grail_agent_import(self):
        """Test that Grail Agent can be imported."""
        from grail_agent_production import GrailAgentProduction
        assert GrailAgentProduction is not None

    def test_grail_agent_initialization(self):
        """Test Grail Agent initialization."""
        from grail_agent_production import GrailAgentProduction
        
        with patch.dict(os.environ, {}, clear=True):
            agent = GrailAgentProduction(mode="demo", bankroll=100)
            assert agent.mode == "demo"
            assert agent.bankroll == 100
            assert agent.trades_executed == 0
            assert agent.predictions_logged == 0

    def test_signal_generation(self):
        """Test signal generation."""
        from grail_agent_production import GrailAgentProduction
        
        with patch.dict(os.environ, {}, clear=True):
            agent = GrailAgentProduction(mode="demo", bankroll=100)
            signal = agent.generate_signal()
            
            assert 'signal' in signal
            assert signal['signal'] in ['BUY', 'SELL', 'HOLD']
            assert 'confidence' in signal
            assert 0.6 <= signal['confidence'] <= 0.95
            assert 'asset' in signal
            assert 'timestamp' in signal

    def test_trade_execution_demo_mode(self):
        """Test trade execution in demo mode."""
        from grail_agent_production import GrailAgentProduction
        
        with patch.dict(os.environ, {}, clear=True):
            agent = GrailAgentProduction(mode="demo", bankroll=100)
            signal = {'signal': 'BUY', 'asset': 'BTC/USDT', 'confidence': 0.85}
            
            initial_trades = agent.trades_executed
            trade = agent.execute_trade(signal)
            
            assert agent.trades_executed == initial_trades + 1
            assert 'id' in trade
            assert 'profit_loss' in trade

    def test_supabase_initialization_no_credentials(self):
        """Test Supabase initialization without credentials."""
        from grail_agent_production import GrailAgentProduction
        
        with patch.dict(os.environ, {}, clear=True):
            agent = GrailAgentProduction(mode="demo", bankroll=100)
            assert agent.supabase is None

    @patch('grail_agent_production.create_client')
    def test_supabase_initialization_with_credentials(self, mock_create_client):
        """Test Supabase initialization with credentials."""
        from grail_agent_production import GrailAgentProduction
        
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test_key'}):
            agent = GrailAgentProduction(mode="demo", bankroll=100)
            assert agent.supabase is not None
            mock_create_client.assert_called_once_with('https://test.supabase.co', 'test_key')


def test_placeholder():
    """Placeholder test to ensure pytest can run."""
    assert 1 + 1 == 2
