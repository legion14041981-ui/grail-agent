#!/usr/bin/env python3
"""
Overlord Sentinel - Baseline Collection & Risk Monitoring
Version: 1.1.0 (With Control Signals Integration)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

Mode: READ-ONLY + LEVEL 1 AUTONOMY
- Baseline collection
- Risk detection
- Control signals reporting
"""

import json
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from overlord_controller import OverlordController, ControlSignal


class RiskAttractor(Enum):
    """Признаки деградации системы"""
    
    # API degradation
    API_SCORE_DROP = "api_score_drop"          # API-first score упал > 20%
    HIGH_UI_FALLBACK = "high_ui_fallback"      # UI fallbacks > 5/сессию
    DEMO_ONLY_MODE = "demo_only_mode"          # Только demo events
    
    # CI degradation
    SMOKE_FAILURES = "smoke_failures"          # Smoke fails
    RUNTIME_SPIKE = "runtime_spike"            # CI время > baseline * 1.5
    CACHE_MISS_RATE = "cache_miss_rate"        # Кэш не работает
    
    # Infrastructure
    SUPABASE_DOWN = "supabase_down"            # Supabase < 95%
    ML_LOAD_SLOW = "ml_load_slow"              # ML > 60s
    PLAYWRIGHT_INIT_FAIL = "playwright_fail"   # Playwright не стартует


class RiskLevel(Enum):
    """Уровень риска"""
    LOW = "low"          # Наблюдение
    MEDIUM = "medium"    # Предупреждение
    HIGH = "high"        # Критичный сигнал


class BaselineCollector:
    """
    Сбор baseline-метрик без изменения поведения
    Пассивный режим: только наблюдение
    """
    
    def __init__(self, baseline_file: str = ".baseline/metrics.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline_file.parent.mkdir(exist_ok=True)
        self.current_session = {
            'timestamp': datetime.now().isoformat(),
            'api_first_score': None,
            'ui_fallbacks': 0,
            'demo_fallbacks': 0,
            'smoke_duration': None,
            'run_duration': None,
            'supabase_success_rate': None
        }
        self.logger = logging.getLogger('BaselineCollector')
    
    def record_metric(self, metric_name: str, value):
        """Записать метрику текущей сессии"""
        self.current_session[metric_name] = value
    
    def save_session(self):
        """Сохранить сессию в baseline file"""
        try:
            # Загрузить существующий baseline
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    baseline = json.load(f)
            else:
                baseline = {'sessions': []}
            
            # Добавить текущую сессию
            baseline['sessions'].append(self.current_session)
            
            # Сохранить
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline, f, indent=2)
            
            self.logger.info(f"✓ Baseline session saved ({len(baseline['sessions'])} total)")
            
        except Exception as e:
            # Не падать при ошибках сохранения
            self.logger.warning(f"Failed to save baseline: {e}")
    
    def get_baseline_summary(self) -> Optional[Dict]:
        """Получить статистику по всем сессиям"""
        if not self.baseline_file.exists():
            return None
        
        try:
            with open(self.baseline_file, 'r') as f:
                baseline = json.load(f)
            
            sessions = baseline['sessions']
            if not sessions:
                return None
            
            # Вычислить статистику
            api_scores = [s['api_first_score'] for s in sessions if s.get('api_first_score') is not None]
            ui_fallbacks = [s['ui_fallbacks'] for s in sessions if s.get('ui_fallbacks') is not None]
            
            return {
                'total_sessions': len(sessions),
                'api_first_score': {
                    'mean': statistics.mean(api_scores) if api_scores else 100.0,
                    'min': min(api_scores) if api_scores else 100.0,
                    'max': max(api_scores) if api_scores else 100.0,
                    'stdev': statistics.stdev(api_scores) if len(api_scores) > 1 else 0.0
                },
                'ui_fallbacks': {
                    'mean': statistics.mean(ui_fallbacks) if ui_fallbacks else 0.0,
                    'max': max(ui_fallbacks) if ui_fallbacks else 0
                },
                'collection_period': {
                    'start': sessions[0]['timestamp'],
                    'end': sessions[-1]['timestamp']
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to load baseline: {e}")
            return None


class RiskSentinel:
    """
    Пассивный мониторинг рисков
    
    Режим: READ-ONLY, NO AUTO-FIX
    Только генерация сигналов
    """
    
    def __init__(self, baseline_collector: BaselineCollector):
        self.baseline = baseline_collector
        self.signals = []
        self.logger = logging.getLogger('RiskSentinel')
    
    def check_risks(self, current_metrics: dict) -> List[Dict]:
        """
        Проверить метрики на признаки деградации
        
        Returns:
            List of risk signals
        """
        self.signals = []
        baseline_summary = self.baseline.get_baseline_summary()
        
        if not baseline_summary:
            # Нет baseline — нет проверок
            self.logger.debug("⚠️  No baseline available, skipping risk checks")
            return []
        
        # Check #1: API-first score
        current_score = current_metrics.get('api_first_score', 100)
        baseline_score = baseline_summary['api_first_score']['mean']
        
        if current_score < baseline_score * 0.8:  # Упал на 20%
            self.signals.append({
                'attractor': RiskAttractor.API_SCORE_DROP.value,
                'level': RiskLevel.MEDIUM.value,
                'message': f"API-first score: {current_score:.1f}% (baseline: {baseline_score:.1f}%)",
                'recommendation': "Проверить WALBI_API_URL availability"
            })
        
        # Check #2: UI fallbacks
        ui_fallbacks = current_metrics.get('ui_fallbacks', 0)
        if ui_fallbacks > 5:
            self.signals.append({
                'attractor': RiskAttractor.HIGH_UI_FALLBACK.value,
                'level': RiskLevel.MEDIUM.value,
                'message': f"UI fallbacks: {ui_fallbacks} (threshold: 5)",
                'recommendation': "API недоступен, проверить endpoint"
            })
        
        # Check #3: Demo-only
        demo_fallbacks = current_metrics.get('demo_fallbacks', 0)
        if demo_fallbacks > 0:
            self.signals.append({
                'attractor': RiskAttractor.DEMO_ONLY_MODE.value,
                'level': RiskLevel.HIGH.value,
                'message': "Fallback to demo events detected",
                'recommendation': "Все scraping методы failed, проверить network"
            })
        
        # Check #4: Supabase health
        supabase_rate = current_metrics.get('supabase_success_rate', 100)
        if supabase_rate < 95.0:
            self.signals.append({
                'attractor': RiskAttractor.SUPABASE_DOWN.value,
                'level': RiskLevel.HIGH.value,
                'message': f"Supabase success rate: {supabase_rate:.1f}% (threshold: 95%)",
                'recommendation': "Проверить Supabase статус и credentials"
            })
        
        self.logger.info(f"🔍 Risk check complete: {len(self.signals)} signals")
        return self.signals
    
    def format_report(self) -> str:
        """Форматировать отчёт о рисках"""
        if not self.signals:
            return "✅ No risk attractors detected\n"
        
        report = "\n⚠️  RISK SENTINEL REPORT\n"
        report += "═" * 50 + "\n\n"
        
        for signal in self.signals:
            level_emoji = {
                RiskLevel.LOW.value: "🟢",
                RiskLevel.MEDIUM.value: "🟡",
                RiskLevel.HIGH.value: "🔴"
            }
            
            report += f"{level_emoji[signal['level']]} {signal['attractor'].upper()}\n"
            report += f"   {signal['message']}\n"
            report += f"   → {signal['recommendation']}\n\n"
        
        return report


class OverlordReport:
    """
    Генерация отчётов Overlord
    Машиночитаемый + человекочитаемый формат
    """
    
    def __init__(self, baseline: BaselineCollector, sentinel: RiskSentinel):
        self.baseline = baseline
        self.sentinel = sentinel
        self.logger = logging.getLogger('OverlordReport')
    
    def generate(self) -> dict:
        """Сгенерировать базовый отчёт"""
        baseline_summary = self.baseline.get_baseline_summary()
        current_session = self.baseline.current_session
        risk_signals = self.sentinel.signals
        
        return {
            'overlord': {
                'version': '1.1.0',
                'timestamp': datetime.now().isoformat(),
                'mode': 'passive_sentinel'
            },
            'baseline': baseline_summary or {'status': 'collecting'},
            'current_session': current_session,
            'risk_assessment': {
                'total_signals': len(risk_signals),
                'by_level': self._count_by_level(risk_signals),
                'signals': risk_signals
            },
            'recommendations': self._generate_recommendations(risk_signals)
        }
    
    def generate_with_control_signals(self, controller: 'OverlordController') -> dict:
        """
        Сгенерировать отчёт с control signals
        
        LEVEL 1 AUTONOMY: добавляет секцию активных сигналов
        """
        base_report = self.generate()  # Базовый отчёт
        
        # Добавить секцию control signals
        active_signals = controller.get_active_signals()
        
        base_report['overlord']['mode'] = 'level_1_autonomy'
        base_report['control_signals'] = {
            'autonomy_level': 'LEVEL_1_SANCTIONED',
            'total_active': len(active_signals),
            'signals': [s.to_dict() for s in active_signals],
            'execution_controls': {
                'force_demo_mode': controller.execution_controls.force_demo_mode,
                'block_live_mode': controller.execution_controls.block_live_mode,
                'disable_ui_fallback': controller.execution_controls.disable_ui_fallback,
                'confidence_threshold': controller.execution_controls.confidence_threshold,
                'max_predictions': controller.execution_controls.max_predictions,
                'ci_early_exit': controller.execution_controls.ci_early_exit
            },
            'decision_log': controller.decision_log[-10:]  # Последние 10 решений
        }
        
        # Рекомендации для человека
        base_report['human_recommendations'] = self._generate_human_recommendations(active_signals)
        
        return base_report
    
    def _generate_human_recommendations(self, signals: List['ControlSignal']) -> List[str]:
        """Генерировать рекомендации для человека"""
        recs = []
        
        # Импорт тут чтобы избежать circular import
        from overlord_controller import ControlSignalType
        
        for signal in signals:
            if signal.signal_type == ControlSignalType.HARD_LIMIT:
                recs.append(f"🔴 REVIEW: {signal.action} (Reason: {signal.reason})")
                recs.append(f"   → Action: Review {signal.attractor.value} root cause")
            
            elif signal.signal_type == ControlSignalType.MODE_DOWNGRADE:
                recs.append(f"🟡 MONITOR: {signal.action}")
                recs.append(f"   → Option: Override if {signal.attractor.value} resolved")
            
            elif signal.signal_type == ControlSignalType.EARLY_EXIT:
                recs.append(f"🟡 ACKNOWLEDGE: {signal.action}")
                recs.append(f"   → Suggested: Investigate {signal.attractor.value}")
        
        if not recs:
            recs.append("✅ No active control signals, system operating normally")
        
        return recs
    
    def _count_by_level(self, signals: List[Dict]) -> dict:
        """Подсчитать сигналы по уровням"""
        counts = {level.value: 0 for level in RiskLevel}
        for signal in signals:
            counts[signal['level']] += 1
        return counts
    
    def _generate_recommendations(self, signals: List[Dict]) -> List[str]:
        """Сгенерировать рекомендации"""
        if not signals:
            return ["System operating within baseline parameters"]
        
        recs = []
        for signal in signals:
            if signal['level'] == RiskLevel.HIGH.value:
                recs.append(f"🔴 URGENT: {signal['recommendation']}")
            elif signal['level'] == RiskLevel.MEDIUM.value:
                recs.append(f"🟡 MONITOR: {signal['recommendation']}")
        
        return recs or ["Review medium/low signals in next maintenance window"]
    
    def format_human_readable(self, report: dict) -> str:
        """Человекочитаемый формат"""
        output = "\n"
        output += "╔" + "═" * 62 + "╗\n"
        output += "║" + " " * 15 + "OVERLORD SENTINEL REPORT" + " " * 23 + "║\n"
        output += "╠" + "═" * 62 + "╣\n"
        output += "║" + " " * 62 + "║\n"
        
        # Baseline status
        baseline = report['baseline']
        if baseline.get('status') == 'collecting':
            output += "║  Baseline: COLLECTING (need 3+ sessions)              ║\n"
        else:
            sessions = baseline['total_sessions']
            api_score = baseline['api_first_score']['mean']
            output += f"║  Baseline: {sessions} sessions collected" + " " * (32 - len(str(sessions))) + "║\n"
            output += f"║  API-first: {api_score:.1f}% (avg)" + " " * (35 - len(f"{api_score:.1f}")) + "║\n"
        
        output += "║" + " " * 62 + "║\n"
        
        # Risk signals
        assessment = report['risk_assessment']
        total = assessment['total_signals']
        output += f"║  Risk Signals: {total}" + " " * (47 - len(str(total))) + "║\n"
        
        by_level = assessment['by_level']
        output += f"║    🔴 High: {by_level['high']}" + " " * (49 - len(str(by_level['high']))) + "║\n"
        output += f"║    🟡 Medium: {by_level['medium']}" + " " * (47 - len(str(by_level['medium']))) + "║\n"
        output += f"║    🟢 Low: {by_level['low']}" + " " * (49 - len(str(by_level['low']))) + "║\n"
        
        output += "║" + " " * 62 + "║\n"
        
        # Control signals (если есть)
        if 'control_signals' in report:
            cs = report['control_signals']
            output += "╠" + "═" * 62 + "╣\n"
            output += "║" + " " * 15 + "CONTROL SIGNALS (LEVEL 1)" + " " * 22 + "║\n"
            output += "╠" + "═" * 62 + "╣\n"
            output += "║" + " " * 62 + "║\n"
            output += f"║  Active Signals: {cs['total_active']}" + " " * (44 - len(str(cs['total_active']))) + "║\n"
            
            controls = cs['execution_controls']
            if controls['force_demo_mode']:
                output += "║    🔴 Force Demo Mode: ACTIVE" + " " * 29 + "║\n"
            if controls['block_live_mode']:
                output += "║    🔴 Block Live Mode: ACTIVE" + " " * 29 + "║\n"
            if controls['disable_ui_fallback']:
                output += "║    🟡 Disable UI Fallback: ACTIVE" + " " * 24 + "║\n"
            if controls['max_predictions']:
                output += f"║    🟡 Prediction Limit: {controls['max_predictions']}" + " " * (33 - len(str(controls['max_predictions']))) + "║\n"
            if controls['ci_early_exit']:
                output += "║    ⚠️  CI Early Exit: ACTIVE" + " " * 30 + "║\n"
            
            output += "║" + " " * 62 + "║\n"
        
        output += "╚" + "═" * 62 + "╝\n"
        
        # Recommendations
        if report.get('human_recommendations'):
            output += "\nHUMAN RECOMMENDATIONS:\n"
            for rec in report['human_recommendations']:
                output += f"  {rec}\n"
        elif report.get('recommendations'):
            output += "\nRECOMMENDATIONS:\n"
            for rec in report['recommendations']:
                output += f"  {rec}\n"
        
        return output
    
    def save_report(self, report: dict, report_dir: str = ".baseline"):
        """Сохранить отчёт в JSON"""
        try:
            report_path = Path(report_dir)
            report_path.mkdir(exist_ok=True)
            
            report_file = report_path / f"report_{int(datetime.now().timestamp())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"✓ Overlord report saved: {report_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save report: {e}")
