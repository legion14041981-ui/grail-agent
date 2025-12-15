#!/usr/bin/env python3
"""
Overlord Verifier - Controlled Autonomy Loop (Level 3)
Version: 1.0.0 (STEP 7 - Verification Layer)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

STEP 7 PHASE 7.1 — Verification Layer

Autonomy Level: 3.0 (Controlled Autonomy Loop)
- Human-applied plans verification
- Actual gain vs Expected gain comparison
- Baseline drift detection
- Rollback recommendation (NO auto-rollback)
- Transparent feedback loop

Critical Restrictions:
- NO auto-apply
- NO auto-rollback
- NO code generation
- Analysis and reporting ONLY
- Human remains in the loop
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from enum import Enum

try:
    from overlord_approver import ApprovedChangePlan
    from overlord_executor import SafeExecutor
except ImportError:
    ApprovedChangePlan = None
    SafeExecutor = None


class VerificationStatus(Enum):
    """
    Статус верификации применённого плана
    """
    SUCCESS = "success"           # План применён корректно, эффект позитивный
    NO_EFFECT = "no_effect"       # План применён, но нет значимого эффекта
    NEGATIVE_EFFECT = "negative"  # План применён, но метрики ухудшились
    PARTIAL_SUCCESS = "partial"   # План применён, но эффект частичный
    VERIFICATION_FAILED = "failed" # Не удалось верифицировать


class ExpectedGainValidator:
    """
    Валидация ожидаемых результатов
    
    STEP 7: Проверяет, что ApprovedChangePlan даёт ожидаемый эффект
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ExpectedGainValidator')
    
    def validate(
        self,
        expected_gain: Dict,
        actual_metrics: Dict
    ) -> Tuple[bool, float, str]:
        """
        Валидировать ожидаемый vs фактический результат
        
        Args:
            expected_gain: {metric_name: expected_value}
            actual_metrics: {metric_name: actual_value}
        
        Returns:
            (is_valid, gain_percentage, reasoning)
        """
        if not expected_gain or not actual_metrics:
            return False, 0.0, "Missing metrics data"
        
        gains = []
        issues = []
        
        for metric_name, expected_value in expected_gain.items():
            if metric_name not in actual_metrics:
                issues.append(f"Metric {metric_name} not in actual results")
                continue
            
            actual_value = actual_metrics[metric_name]
            
            # Рассчитать дельту
            try:
                if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    delta = actual_value - expected_value
                    
                    # Позитивный результат?
                    if delta > 0:
                        percentage = (delta / expected_value * 100) if expected_value != 0 else 100.0
                        gains.append(percentage)
                        self.logger.info(
                            f"✓ {metric_name}: expected {expected_value}, "
                            f"actual {actual_value} (+{percentage:.1f}%)"
                        )
                    elif delta == 0:
                        gains.append(0.0)
                        self.logger.info(f"⊚ {metric_name}: no change")
                    else:
                        self.logger.warning(
                            f"✗ {metric_name}: expected {expected_value}, "
                            f"actual {actual_value} ({delta:.1f})"
                        )
            except Exception as e:
                issues.append(f"{metric_name}: {str(e)}")
        
        if not gains:
            reasoning = "No valid metrics for comparison"
            return False, 0.0, reasoning
        
        avg_gain = sum(gains) / len(gains)
        
        # Проверка: есть ли хотя бы один позитивный метрик?
        has_positive = any(g > 0 for g in gains)
        is_valid = has_positive and avg_gain >= 0
        
        reasoning = f"Avg gain: {avg_gain:+.1f}%"
        if issues:
            reasoning += f" | Issues: {'; '.join(issues[:2])}"
        
        return is_valid, avg_gain, reasoning


class DriftDetector:
    """
    Детектор дрейфа метрик
    
    STEP 7: Сравнивает baseline с post-change метриками
    для обнаружения негативных отклонений
    """
    
    def __init__(self, tolerance_percent: float = 5.0):
        self.tolerance_percent = tolerance_percent  # ±5% допуска
        self.logger = logging.getLogger('DriftDetector')
    
    def detect_drift(
        self,
        baseline_metrics: Dict,
        current_metrics: Dict
    ) -> Tuple[bool, Dict]:
        """
        Обнаружить дрейф метрик
        
        Args:
            baseline_metrics: baseline значения
            current_metrics: текущие значения
        
        Returns:
            (has_drift, drift_report)
        """
        drift_report = {
            'has_drift': False,
            'drift_level': 'none',  # none, minor, significant, critical
            'metrics': {},
            'warnings': []
        }
        
        if not baseline_metrics or not current_metrics:
            return False, drift_report
        
        drifts = []
        critical_drifts = []
        
        for metric_name, baseline_value in baseline_metrics.items():
            if metric_name not in current_metrics:
                continue
            
            current_value = current_metrics[metric_name]
            
            try:
                if isinstance(baseline_value, (int, float)) and isinstance(current_value, (int, float)):
                    if baseline_value == 0:
                        if current_value != 0:
                            drift_pct = 100.0
                        else:
                            drift_pct = 0.0
                    else:
                        drift_pct = abs((current_value - baseline_value) / baseline_value * 100)
                    
                    # Классификация дрейфа
                    if drift_pct > 20:
                        critical_drifts.append({
                            'metric': metric_name,
                            'baseline': baseline_value,
                            'current': current_value,
                            'drift_pct': drift_pct
                        })
                        drift_report['warnings'].append(
                            f"CRITICAL: {metric_name} drifted {drift_pct:.1f}% "
                            f"({baseline_value} → {current_value})"
                        )
                    elif drift_pct > self.tolerance_percent:
                        drifts.append({
                            'metric': metric_name,
                            'baseline': baseline_value,
                            'current': current_value,
                            'drift_pct': drift_pct
                        })
                        self.logger.warning(
                            f"⚠️  {metric_name} drifted {drift_pct:.1f}%"
                        )
                    
                    drift_report['metrics'][metric_name] = {
                        'baseline': baseline_value,
                        'current': current_value,
                        'drift_pct': drift_pct
                    }
            except Exception as e:
                self.logger.warning(f"Failed to compute drift for {metric_name}: {e}")
        
        # Установить уровень дрейфа
        if critical_drifts:
            drift_report['has_drift'] = True
            drift_report['drift_level'] = 'critical'
        elif drifts:
            drift_report['has_drift'] = True
            drift_report['drift_level'] = 'significant'
        else:
            drift_report['drift_level'] = 'none'
        
        return drift_report['has_drift'], drift_report


class ExecutionVerifier:
    """
    Верификатор выполнения ApprovedChangePlan
    
    STEP 7 PHASE 7.1: Проверяет корректность применения плана
    и его фактический эффект
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ExecutionVerifier')
        self.gain_validator = ExpectedGainValidator()
        self.drift_detector = DriftDetector(tolerance_percent=5.0)
        self.verification_dir = Path(".baseline/verifications")
        self.verification_dir.mkdir(parents=True, exist_ok=True)
    
    def verify_execution(
        self,
        approved_plan: ApprovedChangePlan,
        pre_change_baseline: Dict,
        post_change_baseline: Dict,
        execution_metrics: Dict
    ) -> Dict:
        """
        Верифицировать выполнение плана
        
        Args:
            approved_plan: ApprovedChangePlan который был применён
            pre_change_baseline: baseline ДО применения
            post_change_baseline: baseline ПОСЛЕ применения
            execution_metrics: метрики выполнения
        
        Returns:
            Полный отчёт верификации
        """
        self.logger.info(f"🔍 Verifying execution of plan: {approved_plan.plan_id}")
        
        verification = {
            'plan_id': approved_plan.plan_id,
            'verified_at': datetime.now().isoformat(),
            'status': VerificationStatus.VERIFICATION_FAILED.value,
            'expected_gain': approved_plan.plan.expected_gain if hasattr(approved_plan.plan, 'expected_gain') else {},
            'actual_metrics': execution_metrics,
            'pre_change_baseline': pre_change_baseline,
            'post_change_baseline': post_change_baseline,
            'integrity_check': approved_plan.verify_integrity(),
            'gain_validation': None,
            'drift_detection': None,
            'rollback_recommended': False,
            'rollback_justification': None,
            'recommendations': []
        }
        
        # Check 1: Целостность плана
        if not verification['integrity_check']:
            self.logger.error("❌ Integrity check failed: plan was modified")
            verification['status'] = VerificationStatus.VERIFICATION_FAILED.value
            verification['rollback_recommended'] = True
            verification['rollback_justification'] = "Plan integrity compromised"
            return self._save_verification(verification)
        
        # Check 2: Валидация ожидаемого результата
        is_valid, gain_pct, reasoning = self.gain_validator.validate(
            verification['expected_gain'],
            execution_metrics
        )
        
        verification['gain_validation'] = {
            'is_valid': is_valid,
            'gain_percentage': gain_pct,
            'reasoning': reasoning
        }
        
        if not is_valid and gain_pct < 0:
            self.logger.warning(f"⚠️  Negative gain: {gain_pct:.1f}%")
            verification['status'] = VerificationStatus.NEGATIVE_EFFECT.value
            verification['rollback_recommended'] = True
            verification['rollback_justification'] = f"Negative gain: {gain_pct:.1f}%"
        elif gain_pct > 5:
            verification['status'] = VerificationStatus.SUCCESS.value
            self.logger.info(f"✅ Plan execution successful: +{gain_pct:.1f}%")
        elif gain_pct > 0:
            verification['status'] = VerificationStatus.PARTIAL_SUCCESS.value
            self.logger.info(f"⊚ Plan execution partial: +{gain_pct:.1f}%")
        else:
            verification['status'] = VerificationStatus.NO_EFFECT.value
            self.logger.info("⊚ Plan execution: no effect")
        
        # Check 3: Дрейф метрик
        has_drift, drift_report = self.drift_detector.detect_drift(
            pre_change_baseline,
            post_change_baseline
        )
        
        verification['drift_detection'] = drift_report
        
        if drift_report['drift_level'] == 'critical':
            self.logger.error("🚨 CRITICAL DRIFT DETECTED")
            verification['rollback_recommended'] = True
            verification['rollback_justification'] = "Critical drift in metrics"
            verification['recommendations'].append(
                "⚠️  CRITICAL: Severe metric degradation detected. Manual review required."
            )
        elif drift_report['drift_level'] == 'significant':
            self.logger.warning("⚠️  Significant drift detected")
            verification['recommendations'].append(
                "⚠️  WATCH: Monitor metrics closely. Consider rollback if issues persist."
            )
        
        # Финальная рекомендация
        if verification['rollback_recommended']:
            verification['recommendations'].append(
                "💡 Rollback recommended. Execute manually if necessary."
            )
        else:
            verification['recommendations'].append(
                "✓ Plan execution verified. No issues detected."
            )
        
        self.logger.info(
            f"📋 Verification complete: status={verification['status']}, "
            f"gain={gain_pct:.1f}%, rollback_recommended={verification['rollback_recommended']}"
        )
        
        return self._save_verification(verification)
    
    def _save_verification(self, verification: Dict) -> Dict:
        """
        Сохранить отчёт верификации
        """
        try:
            plan_id = verification['plan_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            verification_file = self.verification_dir / f"verification_{plan_id}_{timestamp}.json"
            
            with open(verification_file, 'w') as f:
                json.dump(verification, f, indent=2)
            
            self.logger.info(f"✓ Verification saved: {verification_file}")
            verification['verification_file'] = str(verification_file)
        except Exception as e:
            self.logger.error(f"Failed to save verification: {e}")
        
        return verification
    
    def get_latest_verifications(self, limit: int = 10) -> List[Dict]:
        """
        Получить последние верификации
        """
        try:
            files = sorted(
                self.verification_dir.glob("verification_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            verifications = []
            for file in files:
                try:
                    with open(file, 'r') as f:
                        verifications.append(json.load(f))
                except Exception as e:
                    self.logger.warning(f"Failed to load {file}: {e}")
            
            return verifications
        except Exception as e:
            self.logger.error(f"Failed to get verifications: {e}")
            return []
    
    def generate_verification_summary(self, verifications: List[Dict]) -> Dict:
        """
        Сгенерировать summary верификаций
        
        Returns:
            {status: count, total: N, success_rate: %}
        """
        if not verifications:
            return {
                'total': 0,
                'by_status': {},
                'success_rate': 0.0,
                'rollback_recommended_count': 0
            }
        
        total = len(verifications)
        by_status = {}
        rollback_count = 0
        
        for v in verifications:
            status = v.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
            
            if v.get('rollback_recommended', False):
                rollback_count += 1
        
        success_count = by_status.get(VerificationStatus.SUCCESS.value, 0)
        success_rate = (success_count / total * 100) if total > 0 else 0.0
        
        return {
            'total': total,
            'by_status': by_status,
            'success_rate': success_rate,
            'rollback_recommended_count': rollback_count
        }


class RollbackRecommender:
    """
    Рекомендатор откатов (NO AUTO-ROLLBACK)
    
    STEP 7: Генерирует рекомендации на основе верификации
    Человек принимает финальное решение
    """
    
    def __init__(self):
        self.logger = logging.getLogger('RollbackRecommender')
        self.recommendation_dir = Path(".baseline/rollback_recommendations")
        self.recommendation_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_recommendation(
        self,
        verification: Dict,
        approved_plan: ApprovedChangePlan,
        rollback_manager=None
    ) -> Dict:
        """
        Сгенерировать рекомендацию на откат
        
        Критерии:
        - CRITICAL drift → STRONG recommendation
        - Negative gain → MODERATE recommendation
        - No effect → WEAK recommendation
        - Partial success → MONITOR
        
        Returns:
            Рекомендация (NO auto-execution)
        """
        recommendation = {
            'generated_at': datetime.now().isoformat(),
            'plan_id': approved_plan.plan_id,
            'should_rollback': False,
            'confidence': 0.0,  # 0.0 - 1.0
            'reasoning': [],
            'metrics_summary': {
                'status': verification.get('status'),
                'gain_pct': verification.get('gain_validation', {}).get('gain_percentage', 0),
                'drift_level': verification.get('drift_detection', {}).get('drift_level')
            },
            'rollback_justification': verification.get('rollback_justification'),
            'recommendations': verification.get('recommendations', [])
        }
        
        # Логика рекомендации
        drift_level = verification.get('drift_detection', {}).get('drift_level', 'none')
        status = verification.get('status')
        gain_pct = verification.get('gain_validation', {}).get('gain_percentage', 0)
        
        if drift_level == 'critical':
            recommendation['should_rollback'] = True
            recommendation['confidence'] = 0.95
            recommendation['reasoning'].append("CRITICAL: Severe metric drift detected")
            recommendation['reasoning'].append(f"Confidence: {recommendation['confidence']:.0%}")
        elif status == VerificationStatus.NEGATIVE_EFFECT.value and gain_pct < -5:
            recommendation['should_rollback'] = True
            recommendation['confidence'] = 0.75
            recommendation['reasoning'].append(f"Negative impact: {gain_pct:.1f}%")
            recommendation['reasoning'].append(f"Confidence: {recommendation['confidence']:.0%}")
        elif drift_level == 'significant':
            recommendation['should_rollback'] = False  # Monitor, not rollback
            recommendation['confidence'] = 0.5
            recommendation['reasoning'].append("Monitor: Significant drift but within tolerance")
            recommendation['reasoning'].append("Recommendation: Watch for further degradation")
        else:
            recommendation['should_rollback'] = False
            recommendation['confidence'] = 0.0
            recommendation['reasoning'].append("No rollback needed: Plan executed as expected")
        
        # Сохранить рекомендацию
        self._save_recommendation(recommendation)
        
        return recommendation
    
    def _save_recommendation(self, recommendation: Dict) -> None:
        """
        Сохранить рекомендацию на откат
        """
        try:
            plan_id = recommendation['plan_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rec_file = self.recommendation_dir / f"recommendation_{plan_id}_{timestamp}.json"
            
            with open(rec_file, 'w') as f:
                json.dump(recommendation, f, indent=2)
            
            self.logger.info(f"✓ Recommendation saved: {rec_file}")
        except Exception as e:
            self.logger.error(f"Failed to save recommendation: {e}")
    
    def format_recommendation(self, recommendation: Dict) -> str:
        """
        Форматировать рекомендацию для вывода
        """
        action = "RECOMMEND ROLLBACK" if recommendation['should_rollback'] else "NO ROLLBACK NEEDED"
        confidence = recommendation['confidence']
        
        output = f"""
╔════════════════════════════════════════════════════════════╗
║          ROLLBACK RECOMMENDATION (NO AUTO-EXEC)            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Plan ID:      {recommendation['plan_id']:40s}  ║
║  Action:       {action:40s}  ║
║  Confidence:   {confidence:40.0%}  ║
║                                                            ║
║  Status:       {recommendation['metrics_summary']['status']:40s}  ║
║  Gain:         {recommendation['metrics_summary']['gain_pct']:+39.1f}%  ║
║  Drift Level:  {recommendation['metrics_summary']['drift_level']:40s}  ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║  REASONING:                                                ║
║                                                            ║
"""
        for reason in recommendation['reasoning']:
            output += f"║  • {reason:54s}  ║\n"
        
        output += f"""
╠════════════════════════════════════════════════════════════╣
║  HUMAN ACTION REQUIRED:                                    ║
║                                                            ║
"""
        
        if recommendation['should_rollback']:
            output += "║  1. Review this recommendation                            ║\n"
            output += "║  2. Verify the metrics degradation                       ║\n"
            output += "║  3. Execute MANUAL rollback if necessary                 ║\n"
            output += "║     (NO automatic rollback will occur)                   ║\n"
        else:
            output += "║  • Plan execution verified successfully                 ║\n"
            output += "║  • No human action required                              ║\n"
        
        output += f"""
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"""
        return output
