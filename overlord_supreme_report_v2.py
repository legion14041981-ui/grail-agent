#!/usr/bin/env python3
"""
Overlord Supreme Report v2 - Final Synthesis Report
Version: 2.0.0 (STEP 7)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

STEP 7 PHASE 7.4 — Overlord Supreme Report v2

Расширенный отчёт, объединяющий:
1. Applied Plans (какие планы были применены)
2. Verification Results (как они исполнились)
3. Gain vs Expected Gain (фактический эффект)
4. Drift Warnings (отклонения метрик)
5. Rollback Recommendations (рекомендации на откат)
6. Learning Insights (что научился метаплэннер)

Финальный результат — интегральный взгляд на работу системы.

Autonomy Level: 3.0 (Controlled Autonomy Loop)
Mode: REPORTING ONLY (NO execution)
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

try:
    from overlord_verifier import ExecutionVerifier, VerificationStatus
    from overlord_feedback_loop import CycleOrchestrator, FeedbackRegistry
    from overlord_approver import ApprovedChangePlan
except ImportError:
    ExecutionVerifier = None
    VerificationStatus = None
    CycleOrchestrator = None
    FeedbackRegistry = None
    ApprovedChangePlan = None


class OverlordSupremeReportV2:
    """
    Финальный синтетический отчёт OVERLORD SUPREME
    
    STEP 7: Объединяет все компоненты системы в одном понятном отчёте
    """
    
    def __init__(self):
        self.logger = logging.getLogger('OverlordSupremeReportV2')
        self.report_dir = Path(".baseline/supreme_reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализация компонентов
        self.feedback_registry = FeedbackRegistry()
        self.verifier = ExecutionVerifier() if ExecutionVerifier else None
        self.cycle_orchestrator = CycleOrchestrator() if CycleOrchestrator else None
    
    def generate_comprehensive_report(
        self,
        verifications: List[Dict],
        cycle_statistics: Optional[Dict] = None,
        baseline_snapshots: Optional[Dict] = None
    ) -> Dict:
        """
        Сгенерировать полный интегральный отчёт
        
        Args:
            verifications: список всех верификаций
            cycle_statistics: статистика по циклам (опционально)
            baseline_snapshots: снимки baseline (опционально)
        
        Returns:
            Полный отчёт в формате JSON
        """
        self.logger.info("📋 Generating Overlord Supreme Report v2...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'overlord_version': '2.0.0',
            'autonomy_level': 3.0,
            'step': 7,
            'phase': '7.4',
            'mode': 'REPORTING_ONLY',
            
            # Раздел 1: Применённые планы
            'applied_plans': self._summarize_applied_plans(verifications),
            
            # Раздел 2: Результаты верификации
            'verification_results': self._summarize_verification_results(verifications),
            
            # Раздел 3: Gain Analysis
            'gain_analysis': self._analyze_gains(verifications),
            
            # Раздел 4: Drift Warnings
            'drift_warnings': self._extract_drift_warnings(verifications),
            
            # Раздел 5: Rollback Recommendations
            'rollback_recommendations': self._extract_rollback_recommendations(verifications),
            
            # Раздел 6: Learning Insights
            'learning_insights': self._generate_learning_insights(verifications, cycle_statistics),
            
            # Раздел 7: System Health
            'system_health': self._assess_system_health(verifications, cycle_statistics),
            
            # Раздел 8: Рекомендации на действие
            'action_recommendations': self._generate_action_recommendations(verifications)
        }
        
        # Сохранить отчёт
        self._save_report(report)
        
        return report
    
    def _summarize_applied_plans(self, verifications: List[Dict]) -> Dict:
        """
        Раздел 1: Применённые планы
        """
        total = len(verifications)
        
        by_status = {}
        plan_ids = []
        
        for v in verifications:
            status = v.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
            plan_ids.append(v.get('plan_id'))
        
        return {
            'total_applied': total,
            'by_status': by_status,
            'plan_ids_sample': plan_ids[:10]  # Первые 10 для примера
        }
    
    def _summarize_verification_results(self, verifications: List[Dict]) -> Dict:
        """
        Раздел 2: Результаты верификации
        """
        if not verifications:
            return {'total': 0, 'results': {}}
        
        results = {}
        total = len(verifications)
        
        for v in verifications:
            status = v.get('status', 'unknown')
            if status not in results:
                results[status] = {
                    'count': 0,
                    'percentage': 0.0,
                    'avg_gain': 0.0,
                    'examples': []
                }
            
            results[status]['count'] += 1
            results[status]['avg_gain'] += v.get('gain_validation', {}).get('gain_percentage', 0.0)
            
            # Добавить пример (первый)
            if len(results[status]['examples']) < 2:
                results[status]['examples'].append({
                    'plan_id': v.get('plan_id'),
                    'gain': v.get('gain_validation', {}).get('gain_percentage', 0.0),
                    'integrity_check': v.get('integrity_check')
                })
        
        # Нормализировать средние и проценты
        for status in results:
            count = results[status]['count']
            results[status]['percentage'] = (count / total * 100) if total > 0 else 0.0
            results[status]['avg_gain'] = results[status]['avg_gain'] / count if count > 0 else 0.0
        
        return {
            'total': total,
            'results': results
        }
    
    def _analyze_gains(self, verifications: List[Dict]) -> Dict:
        """
        Раздел 3: Анализ прибыльности (Gain Analysis)
        """
        if not verifications:
            return {
                'total_gain': 0.0,
                'avg_gain': 0.0,
                'max_gain': 0.0,
                'min_gain': 0.0,
                'positive_gains': 0,
                'negative_gains': 0,
                'neutral': 0
            }
        
        gains = []
        positive = 0
        negative = 0
        neutral = 0
        
        for v in verifications:
            gain = v.get('gain_validation', {}).get('gain_percentage', 0.0)
            gains.append(gain)
            
            if gain > 0.5:
                positive += 1
            elif gain < -0.5:
                negative += 1
            else:
                neutral += 1
        
        total_gain = sum(gains)
        avg_gain = total_gain / len(gains) if gains else 0.0
        max_gain = max(gains) if gains else 0.0
        min_gain = min(gains) if gains else 0.0
        
        return {
            'total_gain': total_gain,
            'avg_gain': avg_gain,
            'max_gain': max_gain,
            'min_gain': min_gain,
            'positive_gains': positive,
            'negative_gains': negative,
            'neutral': neutral,
            'positive_rate': (positive / len(gains) * 100) if gains else 0.0
        }
    
    def _extract_drift_warnings(self, verifications: List[Dict]) -> Dict:
        """
        Раздел 4: Предупреждения о дрейфе
        """
        critical_drifts = []
        significant_drifts = []
        minor_drifts = []
        
        for v in verifications:
            drift_report = v.get('drift_detection', {})
            drift_level = drift_report.get('drift_level', 'none')
            
            drift_info = {
                'plan_id': v.get('plan_id'),
                'drift_level': drift_level,
                'warnings': drift_report.get('warnings', [])
            }
            
            if drift_level == 'critical':
                critical_drifts.append(drift_info)
            elif drift_level == 'significant':
                significant_drifts.append(drift_info)
            elif drift_level == 'minor':
                minor_drifts.append(drift_info)
        
        return {
            'total_with_drift': len(critical_drifts) + len(significant_drifts) + len(minor_drifts),
            'critical': {
                'count': len(critical_drifts),
                'examples': critical_drifts[:5]
            },
            'significant': {
                'count': len(significant_drifts),
                'examples': significant_drifts[:5]
            },
            'minor': {
                'count': len(minor_drifts),
                'examples': minor_drifts[:5]
            },
            'summary': f"{len(critical_drifts)} CRITICAL, {len(significant_drifts)} SIGNIFICANT, {len(minor_drifts)} MINOR"
        }
    
    def _extract_rollback_recommendations(self, verifications: List[Dict]) -> Dict:
        """
        Раздел 5: Рекомендации на откат
        """
        rollback_recommended = []
        strong_recommendations = []
        moderate_recommendations = []
        
        for v in verifications:
            if v.get('rollback_recommended', False):
                rec = {
                    'plan_id': v.get('plan_id'),
                    'justification': v.get('rollback_justification'),
                    'status': v.get('status'),
                    'gain': v.get('gain_validation', {}).get('gain_percentage', 0.0)
                }
                rollback_recommended.append(rec)
                
                # Классифицировать по уверенности
                gain = rec['gain']
                if gain < -10 or v.get('status') == 'negative':
                    strong_recommendations.append(rec)
                else:
                    moderate_recommendations.append(rec)
        
        return {
            'total_recommended': len(rollback_recommended),
            'strong_confidence': {
                'count': len(strong_recommendations),
                'examples': strong_recommendations[:3]
            },
            'moderate_confidence': {
                'count': len(moderate_recommendations),
                'examples': moderate_recommendations[:3]
            },
            'action_required': len(strong_recommendations) > 0,
            'summary': f"{len(strong_recommendations)} STRONG, {len(moderate_recommendations)} MODERATE"
        }
    
    def _generate_learning_insights(self, verifications: List[Dict], cycle_stats: Optional[Dict]) -> Dict:
        """
        Раздел 6: Learning Insights — что научился метаплэннер
        """
        insights = {
            'timestamp': datetime.now().isoformat(),
            'total_verifications': len(verifications),
            'key_patterns': []
        }
        
        # Паттерн 1: Успешные планы
        successful = [v for v in verifications if v.get('status') == 'success']
        if successful:
            insights['key_patterns'].append({
                'pattern': 'Successful Plans',
                'count': len(successful),
                'avg_gain': sum(v.get('gain_validation', {}).get('gain_percentage', 0) for v in successful) / len(successful),
                'insight': 'High-gain plans are most common. Continue this strategy.'
            })
        
        # Паттерн 2: Дрейф метрик
        drifts = [v for v in verifications if v.get('drift_detection', {}).get('has_drift', False)]
        if drifts:
            insights['key_patterns'].append({
                'pattern': 'Metric Drifts',
                'count': len(drifts),
                'insight': 'Some plans cause metric drift. Need tighter monitoring.'
            })
        
        # Паттерн 3: Планы без эффекта
        no_effect = [v for v in verifications if v.get('status') == 'no_effect']
        if no_effect:
            insights['key_patterns'].append({
                'pattern': 'No-Effect Plans',
                'count': len(no_effect),
                'insight': 'Some plans have minimal impact. Review relevance.'
            })
        
        # Паттерн 4: Отрицательный эффект
        negative = [v for v in verifications if v.get('status') == 'negative']
        if negative:
            insights['key_patterns'].append({
                'pattern': 'Negative-Effect Plans',
                'count': len(negative),
                'insight': 'ATTENTION: Some plans reduced performance. Require rollback review.'
            })
        
        return insights
    
    def _assess_system_health(self, verifications: List[Dict], cycle_stats: Optional[Dict]) -> Dict:
        """
        Раздел 7: Оценка здоровья системы
        """
        if not verifications:
            return {'health_score': 0.0, 'status': 'NO_DATA'}
        
        total = len(verifications)
        successful = len([v for v in verifications if v.get('status') == 'success'])
        partial = len([v for v in verifications if v.get('status') == 'partial_success'])
        negative = len([v for v in verifications if v.get('status') == 'negative'])
        failed = len([v for v in verifications if v.get('status') == 'verification_failed'])
        
        # Вычислить health score (0-100)
        success_rate = (successful / total * 100) if total > 0 else 0
        partial_rate = (partial / total * 100) if total > 0 else 0
        negative_rate = (negative / total * 100) if total > 0 else 0
        failed_rate = (failed / total * 100) if total > 0 else 0
        
        health_score = (success_rate * 1.0 + partial_rate * 0.7 - negative_rate * 1.5 - failed_rate * 2.0) / 2
        health_score = max(0, min(100, health_score))  # Clamp to 0-100
        
        # Определить статус
        if health_score >= 80:
            status = 'EXCELLENT'
        elif health_score >= 60:
            status = 'GOOD'
        elif health_score >= 40:
            status = 'FAIR'
        else:
            status = 'CRITICAL'
        
        return {
            'health_score': health_score,
            'status': status,
            'breakdown': {
                'successful': successful,
                'partial_success': partial,
                'no_effect': len([v for v in verifications if v.get('status') == 'no_effect']),
                'negative': negative,
                'failed': failed
            },
            'rates': {
                'success_rate': success_rate,
                'partial_rate': partial_rate,
                'negative_rate': negative_rate,
                'failed_rate': failed_rate
            }
        }
    
    def _generate_action_recommendations(self, verifications: List[Dict]) -> List[str]:
        """
        Раздел 8: Рекомендации на действие для человека
        """
        recommendations = []
        
        # Проверка 1: Критический дрейф
        critical_drifts = [v for v in verifications 
                          if v.get('drift_detection', {}).get('drift_level') == 'critical']
        if critical_drifts:
            recommendations.append(
                f"🚨 CRITICAL: {len(critical_drifts)} plans with critical metric drift detected. "
                "Manual review and potential rollback required."
            )
        
        # Проверка 2: Отрицательный эффект
        negative = [v for v in verifications if v.get('status') == 'negative']
        if negative:
            recommendations.append(
                f"⚠️  WARNING: {len(negative)} plans resulted in negative effects. "
                "Recommend reviewing rollback options."
            )
        
        # Проверка 3: Низкий успех
        if len(verifications) >= 5:
            success_rate = len([v for v in verifications if v.get('status') == 'success']) / len(verifications)
            if success_rate < 0.5:
                recommendations.append(
                    "ℹ️  INFO: Success rate below 50%. Consider adjusting plan generation strategy."
                )
        
        # Проверка 4: Положительный тренд
        successful = [v for v in verifications if v.get('status') == 'success']
        if len(successful) >= 3:
            avg_gain = sum(v.get('gain_validation', {}).get('gain_percentage', 0) for v in successful) / len(successful)
            if avg_gain > 10:
                recommendations.append(
                    f"✅ SUCCESS: {len(successful)} successful plans with avg gain {avg_gain:.1f}%. "
                    "Current strategy is effective."
                )
        
        # Проверка 5: Отсутствие данных
        if not verifications:
            recommendations.append(
                "ℹ️  INFO: No verifications yet. Awaiting first execution cycle."
            )
        
        return recommendations
    
    def _save_report(self, report: Dict) -> None:
        """
        Сохранить отчёт в файл
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.report_dir / f"supreme_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"✅ Supreme report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save supreme report: {e}")
    
    def format_supreme_report(self, report: Dict) -> str:
        """
        Отформатировать отчёт для вывода в консоль
        """
        output = f"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                    ║
║                        OVERLORD SUPREME REPORT v2.0.0                                            ║
║                       STEP 7 — CONTROLLED AUTONOMY LOOP                                          ║
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
║  Generated: {report['generated_at']:75s}  ║
║  Autonomy Level: {report['autonomy_level']} | Mode: {report['mode']:59s}  ║
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 1: APPLIED PLANS                                                                       ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        applied = report['applied_plans']
        output += f"║  Total Applied: {applied['total_applied']:87d}  ║\n"
        output += "║  By Status:\n"
        for status, count in applied['by_status'].items():
            output += f"║    • {status:30s}: {count:3d}                                         ║\n"
        
        output += f"""
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 2: GAIN ANALYSIS                                                                       ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        gain = report['gain_analysis']
        output += f"║  Total Gain: {gain['total_gain']:+8.2f}%\n"
        output += f"║  Average Gain: {gain['avg_gain']:+8.2f}%\n"
        output += f"║  Max Gain: {gain['max_gain']:+8.2f}% | Min Gain: {gain['min_gain']:+8.2f}%\n"
        output += f"║  Positive Plans: {gain['positive_gains']:3d} ({gain['positive_rate']:5.1f}%) | Negative: {gain['negative_gains']:3d}\n"
        
        output += f"""
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 3: DRIFT WARNINGS                                                                      ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        drift = report['drift_warnings']
        output += f"║  Total with Drift: {drift['total_with_drift']:70d}  ║\n"
        output += f"║  Summary: {drift['summary']:80s}  ║\n"
        
        output += f"""
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 4: ROLLBACK RECOMMENDATIONS                                                            ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        rollback = report['rollback_recommendations']
        output += f"║  Total Recommended: {rollback['total_recommended']:69d}  ║\n"
        output += f"║  Summary: {rollback['summary']:80s}  ║\n"
        output += f"║  Action Required: {str(rollback['action_required']):73s}  ║\n"
        
        output += f"""
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 5: SYSTEM HEALTH                                                                       ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        health = report['system_health']
        output += f"║  Health Score: {health['health_score']:6.1f}/100 ({health['status']:7s})\n"
        output += f"║  Success Rate: {health['rates']['success_rate']:6.1f}% | Partial: {health['rates']['partial_rate']:6.1f}%\n"
        output += f"║  Negative: {health['rates']['negative_rate']:6.1f}% | Failed: {health['rates']['failed_rate']:6.1f}%\n"
        
        output += f"""
║                                                                                                    ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  SECTION 6: ACTION RECOMMENDATIONS                                                              ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                    ║
"""
        
        for i, rec in enumerate(report['action_recommendations'], 1):
            output += f"║  {i}. {rec[:92]}\n"
        
        output += f"""
║                                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        
        return output
