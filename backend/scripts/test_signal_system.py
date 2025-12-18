"""
Test Script for Signal System
Compare V1 vs V1+V2 performance
"""

import sys
sys.path.append('..')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.integrated_signal_manager import IntegratedSignalManager
from strategies.technical_indicators import TechnicalIndicators


def generate_sample_data(periods=200):
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='5min')
    
    # Generate realistic price movement
    base_price = 50000
    returns = np.random.normal(0.0001, 0.002, periods)
    prices = base_price * (1 + returns).cumprod()
    
    data = {
        'timestamp': dates,
        'open': prices + np.random.uniform(-50, 50, periods),
        'high': prices + np.random.uniform(0, 100, periods),
        'low': prices - np.random.uniform(0, 100, periods),
        'close': prices,
        'volume': np.random.uniform(100, 1000, periods)
    }
    
    df = pd.DataFrame(data)
    
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    # Add current_price for indicators
    df['current_price'] = df['close']
    
    return df


def test_signal_generation():
    """Test basic signal generation"""
    print("=" * 80)
    print("TEST 1: Basic Signal Generation")
    print("=" * 80)
    
    # Generate sample data
    df = generate_sample_data()
    
    # Initialize signal manager
    signal_manager = IntegratedSignalManager(use_v2_validation=True)
    
    # Generate signal
    print("\nGenerating signal...")
    signal = signal_manager.generate_signal(df, 'BTC/USDT:USDT')
    
    # Display results
    print("\n--- SIGNAL OUTPUT ---")
    print(f"Action: {signal['action']}")
    print(f"Confidence: {signal['confidence']:.2%}")
    print(f"Price: ${signal['current_price']:,.2f}")
    print(f"Stop Loss: ${signal['stop_loss']:,.2f}")
    print(f"Take Profit: ${signal['take_profit']:,.2f}")
    print(f"Risk/Reward: {signal['risk_reward']:.2f}")
    
    print("\n--- V1 ANALYSIS ---")
    print(f"Raw Score: {signal['raw_score']:.3f}")
    print(f"Adjusted Score: {signal['adjusted_score']:.3f}")
    print(f"Volatility Factor: {signal['volatility_factor']:.3f}")
    print(f"Regime Valid: {signal['regime_valid']}")
    
    print("\n--- CATEGORY SCORES ---")
    for category, score in signal['category_scores'].items():
        direction = "BULL" if score > 0 else "BEAR"
        print(f"{category:18s}: {score:6.3f} ({direction})")
    
    print("\n--- V2 VALIDATION ---")
    print(f"Valid: {signal['validation']['is_valid']}")
    print(f"Confirmation: {signal['validation']['confirmation_score']:.1f}%")
    print(f"Strength: {signal['validation']['signal_strength']}")
    print(f"Market: {signal['validation']['market_condition']}")
    
    print("\n--- REASONING ---")
    print(signal['explanation']['reasoning'])
    
    print("\n--- SUPPORTING INDICATORS ---")
    for ind in signal['explanation']['supporting_indicators']:
        print(f"  • {ind[0]}: {ind[1]}")
    
    print("\n✅ Test 1 passed!")


def test_v1_vs_v2():
    """Compare V1 only vs V1+V2"""
    print("\n" + "=" * 80)
    print("TEST 2: V1 vs V1+V2 Comparison")
    print("=" * 80)
    
    # Generate sample data
    df = generate_sample_data()
    
    # Initialize both versions
    v1_only = IntegratedSignalManager(use_v2_validation=False)
    v1_v2 = IntegratedSignalManager(use_v2_validation=True)
    
    # Generate signals
    print("\nGenerating signals with both systems...")
    signal_v1 = v1_only.generate_signal(df, 'BTC/USDT:USDT')
    signal_v2 = v1_v2.generate_signal(df, 'BTC/USDT:USDT')
    
    # Compare
    print("\n--- COMPARISON ---")
    print(f"\n{'Metric':<25} {'V1 Only':<20} {'V1+V2'}")
    print("-" * 80)
    print(f"{'Action':<25} {signal_v1['action']:<20} {signal_v2['action']}")
    print(f"{'Confidence':<25} {signal_v1['confidence']:.3f}{'':<17} {signal_v2['confidence']:.3f}")
    print(f"{'V1 Raw Score':<25} {signal_v1['raw_score']:.3f}{'':<17} {signal_v2['raw_score']:.3f}")
    print(f"{'V1 Adjusted Score':<25} {signal_v1['adjusted_score']:.3f}{'':<17} {signal_v2['adjusted_score']:.3f}")
    
    if 'validation' in signal_v2:
        print(f"{'V2 Confirmation':<25} {'N/A':<20} {signal_v2['validation']['confirmation_score']:.1f}%")
        print(f"{'V2 Valid':<25} {'N/A':<20} {signal_v2['validation']['is_valid']}")
    
    print(f"{'Processing Time':<25} {signal_v1['processing_time_ms']:.1f}ms{'':<13} {signal_v2['processing_time_ms']:.1f}ms")
    
    # Decision analysis
    if signal_v1['action'] != signal_v2['action']:
        print("\n⚠️  ACTIONS DIFFER!")
        print(f"V1: {signal_v1['action']}")
        print(f"V2: {signal_v2['action']}")
        print(f"Reason: {signal_v2['final_decision'].get('decision_reason', 'unknown')}")
    else:
        print("\n✅ Both systems agree on action")
    
    print("\n✅ Test 2 passed!")


def test_multiple_signals():
    """Test signal generation over time"""
    print("\n" + "=" * 80)
    print("TEST 3: Multiple Signal Generation")
    print("=" * 80)
    
    # Generate longer dataset
    df = generate_sample_data(periods=500)
    
    signal_manager = IntegratedSignalManager(use_v2_validation=True)
    
    # Generate signals at different points
    signals = []
    test_points = [200, 250, 300, 350, 400, 450]
    
    print("\nGenerating signals at different time points...")
    for i, point in enumerate(test_points):
        df_slice = df.iloc[:point]
        signal = signal_manager.generate_signal(df_slice, 'BTC/USDT:USDT')
        signals.append(signal)
        print(f"  Point {i+1}: {signal['action']:<15} Conf: {signal['confidence']:.3f}")
    
    # Statistics
    stats = signal_manager.get_signal_statistics()
    
    print("\n--- SIGNAL STATISTICS ---")
    print(f"Total Signals: {stats['total_signals']}")
    print(f"Long Signals: {stats['long_signals']} ({stats['long_percentage']:.1f}%)")
    print(f"Short Signals: {stats['short_signals']} ({stats['short_percentage']:.1f}%)")
    print(f"Wait Signals: {stats['wait_signals']} ({stats['wait_percentage']:.1f}%)")
    print(f"Avg Confidence: {stats['avg_confidence']:.3f}")
    print(f"V2 Validation Rate: {stats['v2_validation_rate']:.1f}%")
    
    print("\n✅ Test 3 passed!")


def test_indicator_calculation():
    """Test that all 16 indicators work"""
    print("\n" + "=" * 80)
    print("TEST 4: Indicator Calculation")
    print("=" * 80)
    
    df = generate_sample_data()
    
    indicators = TechnicalIndicators()
    result = indicators.calculate_all(df)
    
    expected_indicators = [
        'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'stoch_k', 'stoch_d',
        'ema_9', 'ema_20', 'ema_50', 'ema_200', 'sma_20',
        'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'atr',
        'adx', 'cci', 'mfi', 'obv', 'vwap',
        'mc_probability', 'mc_expected_price',
        'gk_volatility', 'z_score', 'lr_slope'
    ]
    
    print("\nChecking all indicators...")
    missing = []
    for ind in expected_indicators:
        if ind in result:
            print(f"  ✅ {ind}: {result[ind]:.4f}" if isinstance(result[ind], float) else f"  ✅ {ind}: {result[ind]}")
        else:
            print(f"  ❌ {ind}: MISSING")
            missing.append(ind)
    
    if missing:
        print(f"\n❌ Missing indicators: {missing}")
        return False
    
    print(f"\n✅ All {len(expected_indicators)} indicators working!")
    print("\n✅ Test 4 passed!")


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  AI TRADING SIGMA - SIGNAL SYSTEM TEST SUITE".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    tests = [
        ("Indicator Calculation", test_indicator_calculation),
        ("Basic Signal Generation", test_signal_generation),
        ("V1 vs V1+V2 Comparison", test_v1_vs_v2),
        ("Multiple Signals", test_multiple_signals)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ Test '{name}' FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    print("=" * 80)


if __name__ == '__main__':
    run_all_tests()
