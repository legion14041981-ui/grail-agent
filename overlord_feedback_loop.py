#!/usr/bin/env python3
"""
Overlord Feedback Loop - Verification → Metaplanner Integration
Version: 1.0.0 (STEP 7 PHASE 7.2)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

STEP 7 PHASE 7.2 — Feedback Loop Integration

Closed-Loop Cycle:
  PLAN → APPROVE → EXECUTE → VERIFY → ENRICH_BASELINE → NEXT_PLAN
  (Rinse and repeat)

Key Components:
- VerificationFeedback: results from ExecutionVerifier
- BaselineEnricher: updates baseline with post-change metrics
- FeedbackRegistry: tracks verification results
- CycleOrchestrator: manages the full loop

Autonomy Level: 3.0 (Controlled Autonomy Loop)
- Verification feedback enriches baseline
- Plans marked SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE
- Metaplanner learns from execution results
- No manual intervention needed for enrichment
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

try:
    from overlord_verifier import ExecutionVerifier, VerificationStatus
    from overlord_sentinel import BaselineCollector
except ImportError:
    ExecutionVerifier = None
    VerificationStatus = None
    BaselineCollector = None


class PlanOutcome(Enum):
    """
    Итоговый результат плана после выполнения и верификации
    """
    SUCCESS = "success"                # Отличный результат, выше ожиданий
    PARTIAL_SUCCESS = "partial_success" # Хороший результат, в пределах ожиданий
    NO_EFFECT = "no_effect"           # План применён, но эффекта нет
    NEGATIVE_EFFECT = "negative"      # План применён, но метрики ухудшились
    VERIFICATION_FAILED = "failed"     # Не удалось верифицировать
    ROLLED_BACK = "rolled_back"       # План откачен (manual)


class VerificationFeedback:
    """
    Отзыв об исполнении плана с результатами верификации
    
    STEP 7.2: Промежуточный объект, который передаётся
    от ExecutionVerifier к BaselineEnricher
    """
    
    def __init__(self, verification: Dict, outcome: PlanOutcome):
        self.plan_id = verification['plan_id']
        self.verified_at = datetime.fromisoformat(verification['verified_at'])
        self.verification_status = verification['status']
        self.outcome = outcome
        self.gain_pct = verification.get('gain_validation', {}).get('gain_percentage', 0.0)
        self.drift_report = verification.get('drift_detection', {})
        self.actual_metrics = verification.get('actual_metrics', {})
        self.pre_change_baseline = verification.get('pre_change_baseline', {})
        self.post_change_baseline = verification.get('post_change_baseline', {})
        self.rollback_recommended = verification.get('rollback_recommended', False)
        self.verification_file = verification.get('verification_file')
    
    def to_dict(self) -> Dict:
        """Сериализовать в словарь"""
        return {
            'plan_id': self.plan_id,
            'verified_at': self.verified_at.isoformat(),
            'verification_status': self.verification_status,
            'outcome': self.outcome.value,
            'gain_pct': self.gain_pct,
            'drift_report': self.drift_report,
            'rollback_recommended': self.rollback_recommended
        }


class BaselineEnricher:
    """
    Обогащение baseline на основе результатов верификации
    
    STEP 7.2: После успешного применения плана обновляет baseline
    с новыми значениями метрик для использования в будущих планах
    
    Critical: НЕ выполняется если план был откачен
    """
    
    def __init__(self):
        self.logger = logging.getLogger('BaselineEnricher')
        self.enrichment_dir = Path(".baseline/enrichments")
        self.enrichment_dir.mkdir(parents=True, exist_ok=True)
    
    def enrich_baseline(
        self,
        feedback: VerificationFeedback,
        baseline_collector: BaselineCollector = None
    ) -> bool:
        """
        Обогатить baseline на основе отзыва об исполнении
        
        Args:
            feedback: VerificationFeedback от выполнения плана
            baseline_collector: экземпляр BaselineCollector для обновления
        
        Returns:
            True если успешно обогащено, False иначе
        """
        # Проверка: не откачен ли план
        if feedback.outcome == PlanOutcome.ROLLED_BACK:
            self.logger.info(
                f"⏮️  Skipping enrichment: plan {feedback.plan_id} was rolled back"
            )
            return False
        
        # Проверка: достаточно ли положительный результат для обогащения
        if feedback.outcome in [PlanOutcome.SUCCESS, PlanOutcome.PARTIAL_SUCCESS]:
            self.logger.info(
                f"✓ Enriching baseline from successful plan: {feedback.plan_id}"
            )
            
            enrichment_record = {
                'plan_id': feedback.plan_id,
                'enriched_at': datetime.now().isoformat(),
                'outcome': feedback.outcome.value,
                'gain_pct': feedback.gain_pct,
                'pre_change_baseline': feedback.pre_change_baseline,
                'post_change_baseline': feedback.post_change_baseline,
                'actual_metrics': feedback.actual_metrics
            }
            
            # Сохранить запись об обогащении
            self._save_enrichment(enrichment_record)
            
            # Обновить BaselineCollector если предоставлен
            if baseline_collector:
                try:
                    # Записать новые метрики в baseline
                    for metric_name, metric_value in feedback.post_change_baseline.items():
                        baseline_collector.record_metric(metric_name, metric_value)
                    
                    self.logger.info(
                        f"✓ BaselineCollector updated with {len(feedback.post_change_baseline)} metrics"
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update BaselineCollector: {e}")
            
            return True
        
        elif feedback.outcome == PlanOutcome.NO_EFFECT:
            self.logger.info(
                f"⚠️  Plan had no effect: {feedback.plan_id}. Not enriching baseline."
            )
            return False
        
        else:  # NEGATIVE_EFFECT, VERIFICATION_FAILED
            self.logger.warning(
                f"✗ Plan execution failed: {feedback.plan_id}. Not enriching baseline."
            )
            return False
    
    def _save_enrichment(self, enrichment_record: Dict) -> None:
        """Сохранить запись об обогащении"""
        try:
            plan_id = enrichment_record['plan_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            enrichment_file = self.enrichment_dir / f"enrichment_{plan_id}_{timestamp}.json"
            
            with open(enrichment_file, 'w') as f:
                json.dump(enrichment_record, f, indent=2)
            
            self.logger.debug(f"✓ Enrichment saved: {enrichment_file}")
        except Exception as e:
            self.logger.error(f"Failed to save enrichment: {e}")
    
    def get_enrichment_history(self, limit: int = 20) -> List[Dict]:
        """Получить историю обогащений"""
        try:
            files = sorted(
                self.enrichment_dir.glob("enrichment_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            enrichments = []
            for file in files:
                try:
                    with open(file, 'r') as f:
                        enrichments.append(json.load(f))
                except Exception as e:
                    self.logger.warning(f"Failed to load {file}: {e}")
            
            return enrichments
        except Exception as e:
            self.logger.error(f"Failed to get enrichment history: {e}")
            return []


class FeedbackRegistry:
    """
    Реестр всех верификационных отзывов
    
    STEP 7.2: Отслеживает результаты выполнения всех планов
    Используется для анализа эффективности и обучения метапланнера
    """
    
    def __init__(self):
        self.logger = logging.getLogger('FeedbackRegistry')
        self.registry_dir = Path(".baseline/feedback_registry")
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.feedbacks: List[VerificationFeedback] = []
        self._load_existing()
    
    def register_feedback(self, feedback: VerificationFeedback) -> None:
        """Зарегистрировать отзыв об исполнении"""
        self.feedbacks.append(feedback)
        self._save_feedback(feedback)
        
        self.logger.info(
            f"✓ Registered feedback: plan_id={feedback.plan_id}, "
            f"outcome={feedback.outcome.value}"
        )
    
    def _save_feedback(self, feedback: VerificationFeedback) -> None:
        """Сохранить отзыв в файл"""
        try:
            plan_id = feedback.plan_id
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            feedback_file = self.registry_dir / f"feedback_{plan_id}_{timestamp}.json"
            
            with open(feedback_file, 'w') as f:
                json.dump(feedback.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save feedback: {e}")
    
    def _load_existing(self) -> None:
        """Загрузить существующие отзывы из файлов"""
        try:
            files = sorted(
                self.registry_dir.glob("feedback_*.json"),
                key=lambda x: x.stat().st_mtime
            )
            
            for file in files[-100:]:  # Load последние 100
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                    # TODO: Восстановить VerificationFeedback из JSON
                except Exception as e:
                    self.logger.debug(f"Failed to load {file}: {e}")
        except Exception as e:
            self.logger.debug(f"Failed to load existing feedbacks: {e}")
    
    def get_statistics(self) -> Dict:
        """Получить статистику всех отзывов"""
        if not self.feedbacks:
            return {
                'total': 0,
                'by_outcome': {},
                'avg_gain': 0.0,
                'success_rate': 0.0
            }
        
        total = len(self.feedbacks)
        by_outcome = {}
        total_gain = 0.0
        successful = 0
        
        for feedback in self.feedbacks:
            outcome = feedback.outcome.value
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
            total_gain += feedback.gain_pct
            
            if feedback.outcome in [PlanOutcome.SUCCESS, PlanOutcome.PARTIAL_SUCCESS]:
                successful += 1
        
        avg_gain = total_gain / total if total > 0 else 0.0
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return {
            'total': total,
            'by_outcome': by_outcome,
            'avg_gain': avg_gain,
            'success_rate': success_rate
        }


class CycleOrchestrator:
    """
    Координатор полного замкнутого цикла
    
    STEP 7.2: Управляет всем циклом:
    PLAN → APPROVE → EXECUTE → VERIFY → ENRICH → NEXT_PLAN
    
    Нет автоматизации: каждый шаг требует контроля или явного вызова
    """
    
    def __init__(
        self,
        baseline_collector: BaselineCollector = None
    ):
        self.logger = logging.getLogger('CycleOrchestrator')
        self.baseline_collector = baseline_collector
        self.feedback_registry = FeedbackRegistry()
        self.baseline_enricher = BaselineEnricher()
        self.verifier = ExecutionVerifier() if ExecutionVerifier else None
    
    def process_cycle(
        self,
        verification: Dict,
        approved_plan=None
    ) -> Optional[VerificationFeedback]:
        """
        Обработать один полный цикл верификации
        
        Args:
            verification: результат от ExecutionVerifier.verify_execution()
            approved_plan: оригинальный ApprovedChangePlan
        
        Returns:
            VerificationFeedback если успешно, None иначе
        """
        # Шаг 1: Определить исход
        status = verification.get('status')
        rollback_recommended = verification.get('rollback_recommended', False)
        
        outcome = self._determine_outcome(status, rollback_recommended)
        
        self.logger.info(
            f"📊 Cycle processing: status={status}, outcome={outcome.value}"
        )
        
        # Шаг 2: Создать feedback
        feedback = VerificationFeedback(verification, outcome)
        
        # Шаг 3: Зарегистрировать feedback
        self.feedback_registry.register_feedback(feedback)
        
        # Шаг 4: Обогатить baseline (если результат успешный)
        enriched = self.baseline_enricher.enrich_baseline(
            feedback,
            self.baseline_collector
        )
        
        if enriched:
            self.logger.info(
                f"✓ Baseline enriched from plan: {feedback.plan_id}"
            )
        else:
            self.logger.info(
                f"⚠️  Baseline NOT enriched: outcome={outcome.value}"
            )
        
        return feedback
    
    def _determine_outcome(self, status: str, rollback_recommended: bool) -> PlanOutcome:
        """
        Определить итоговый результат на основе статуса верификации
        """
        if rollback_recommended:
            return PlanOutcome.NEGATIVE_EFFECT
        
        status_map = {
            VerificationStatus.SUCCESS.value: PlanOutcome.SUCCESS,
            VerificationStatus.PARTIAL_SUCCESS.value: PlanOutcome.PARTIAL_SUCCESS,
            VerificationStatus.NO_EFFECT.value: PlanOutcome.NO_EFFECT,
            VerificationStatus.NEGATIVE_EFFECT.value: PlanOutcome.NEGATIVE_EFFECT,
            VerificationStatus.VERIFICATION_FAILED.value: PlanOutcome.VERIFICATION_FAILED
        }
        
        return status_map.get(status, PlanOutcome.VERIFICATION_FAILED)
    
    def get_cycle_statistics(self) -> Dict:
        """Получить статистику циклов"""
        return self.feedback_registry.get_statistics()
    
    def format_cycle_report(self) -> str:
        """Отформатировать отчёт по циклам"""
        stats = self.get_cycle_statistics()
        
        if stats['total'] == 0:
            return "No cycles processed yet."
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║          CONTROLLED AUTONOMY LOOP STATISTICS                   ║
║                 (STEP 7 PHASE 7.2)                             ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Total Cycles:      {stats['total']:3d}                                  ║
║  Success Rate:      {stats['success_rate']:6.1f}%                            ║
║  Avg Gain:          {stats['avg_gain']:+6.1f}%                             ║
║                                                                ║
║  Results by Outcome:                                           ║
"""
        
        for outcome, count in sorted(stats['by_outcome'].items()):
            report += f"║    {outcome:20s}: {count:3d}                          ║\n"
        
        report += f"""
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"""
        return report
