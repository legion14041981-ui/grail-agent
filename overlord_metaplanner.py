#!/usr/bin/env python3
"""
Overlord Meta-Planner - Autonomous CI Meta-Planning Layer
Version: 1.0.0 (Level 2 Autonomy)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

ULTRA-BLACK PROTOCOL:
- Analyzes baseline and generates change proposals
- NO automatic application
- NO code generation
- Analysis + planning ONLY

Autonomy Level: LEVEL 2 (Meta-Planning)
- Can propose changes
- Can classify risks
- Can estimate impact
- CANNOT apply changes
- CANNOT modify execution
"""

import json
import time
import random
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class ChangePlanScope(Enum):
    """Область предлагаемых изменений"""
    PARAMETER = "parameter"          # Thresholds, limits, TTL
    LOGIC = "logic"                  # Conditions, guards, flow
    ARCHITECTURE = "architecture"    # Structure, modules, design


class ChangePlanRisk(Enum):
    """Классификация уровня риска"""
    SAFE = "safe"              # LEVEL A: Auto-apply candidate (future)
    REVIEW = "review"          # LEVEL B: Human review required
    FORBIDDEN = "forbidden"    # LEVEL C: Not allowed


class ChangePlan:
    """
    Meta-planning artifact: декларирует ЧТО можно изменить
    
    ULTRA-BLACK COMPLIANCE:
    - Нет генерации кода
    - Нет исполнения
    - Только анализ + рекомендация
    """
    
    def __init__(
        self,
        description: str,
        scope: ChangePlanScope,
        justification: str,
        expected_gain: str,
        affected_parameters: Optional[List[str]] = None
    ):
        self.id = f"plan_{int(time.time())}_{random.randint(1000, 9999)}"
        self.created_at = datetime.now()
        self.description = description
        self.scope = scope
        
        # Risk classification
        self.risk_level = self._classify_risk(scope)
        
        # Justification (metrics-based)
        self.justification = justification
        self.metrics_evidence = {}  # Baseline references
        
        # Expected outcome
        self.expected_gain = expected_gain
        self.estimated_impact = None  # e.g., "API score +10%"
        
        # Affected components
        self.affected_files = []
        self.affected_parameters = affected_parameters or []
        
        # Safety
        self.rollback_strategy = "Automatic TTL expiration" if scope == ChangePlanScope.PARAMETER else "Manual rollback"
        self.requires_human_approval = (self.risk_level != ChangePlanRisk.SAFE)
        
        # Status
        self.status = "proposed"  # proposed / approved / rejected / applied
        self.approved_by = None
        self.approved_at = None
    
    def _classify_risk(self, scope: ChangePlanScope) -> ChangePlanRisk:
        """Классифицировать риск на основе scope"""
        if scope == ChangePlanScope.PARAMETER:
            return ChangePlanRisk.SAFE  # LEVEL A
        elif scope == ChangePlanScope.LOGIC:
            return ChangePlanRisk.REVIEW  # LEVEL B
        else:
            return ChangePlanRisk.FORBIDDEN  # LEVEL C
    
    def to_dict(self) -> dict:
        """Сериализация в JSON"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'description': self.description,
            'scope': self.scope.value,
            'risk_level': self.risk_level.value,
            'justification': self.justification,
            'metrics_evidence': self.metrics_evidence,
            'expected_gain': self.expected_gain,
            'estimated_impact': self.estimated_impact,
            'affected_files': self.affected_files,
            'affected_parameters': self.affected_parameters,
            'rollback_strategy': self.rollback_strategy,
            'requires_human_approval': self.requires_human_approval,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


class MetaPlanner:
    """
    Autonomous CI Meta-Planner
    
    Анализирует baseline, decision log, risk signals
    Генерирует change proposals
    
    ULTRA-BLACK COMPLIANCE:
    - READ-ONLY analysis
    - NO execution changes
    - NO automatic application
    """
    
    def __init__(self, baseline_collector, risk_sentinel):
        self.baseline = baseline_collector
        self.sentinel = risk_sentinel
        self.logger = logging.getLogger('MetaPlanner')
    
    def analyze_and_plan(self, current_metrics: dict, decision_log: List[dict]) -> List[ChangePlan]:
        """
        Анализировать состояние и сгенерировать планы
        
        Returns:
            List of ChangePlan proposals
        """
        plans = []
        
        baseline_summary = self.baseline.get_baseline_summary()
        if not baseline_summary:
            self.logger.debug("⚠️  No baseline available for meta-planning")
            return plans
        
        # Analysis #1: API-first score degradation
        api_trend = self._analyze_api_first_trend(baseline_summary, current_metrics)
        if api_trend:
            plans.append(api_trend)
        
        # Analysis #2: UI fallback frequency
        ui_plan = self._analyze_ui_fallback_pattern(baseline_summary, current_metrics)
        if ui_plan:
            plans.append(ui_plan)
        
        # Analysis #3: Control signal effectiveness
        signal_plan = self._analyze_control_signal_patterns(decision_log)
        if signal_plan:
            plans.append(signal_plan)
        
        self.logger.info(f"🧠 Meta-Planner: {len(plans)} change plans generated")
        return plans
    
    def _analyze_api_first_trend(self, baseline: dict, current: dict) -> Optional[ChangePlan]:
        """Анализ тренда API-first score"""
        baseline_score = baseline['api_first_score']['mean']
        current_score = current.get('api_first_score', 100.0)
        
        # Если API score стабильно ниже baseline
        if current_score < baseline_score * 0.9 and baseline['total_sessions'] >= 3:
            plan = ChangePlan(
                description="Increase API retry attempts before UI fallback",
                scope=ChangePlanScope.PARAMETER,
                justification=f"API-first score: {current_score:.1f}% vs baseline {baseline_score:.1f}%. "
                              f"Consistent degradation over {baseline['total_sessions']} sessions.",
                expected_gain="Reduce UI fallbacks by 20-30%, improve API-first compliance",
                affected_parameters=['api_retry_count', 'api_timeout']
            )
            plan.metrics_evidence = {
                'baseline_api_score': baseline_score,
                'current_api_score': current_score,
                'sessions_analyzed': baseline['total_sessions']
            }
            plan.estimated_impact = f"API score: {current_score:.1f}% → {baseline_score:.1f}%"
            return plan
        
        return None
    
    def _analyze_ui_fallback_pattern(self, baseline: dict, current: dict) -> Optional[ChangePlan]:
        """Анализ паттерна UI fallbacks"""
        baseline_ui = baseline['ui_fallbacks']['mean']
        current_ui = current.get('ui_fallbacks', 0)
        
        # Если UI fallbacks стабильно высокие
        if current_ui > 3 and baseline_ui > 2:
            plan = ChangePlan(
                description="Adjust API endpoint health check interval",
                scope=ChangePlanScope.PARAMETER,
                justification=f"UI fallbacks: {current_ui} (baseline avg: {baseline_ui:.1f}). "
                              f"API may be temporarily unavailable. Recommend health check before fallback.",
                expected_gain="Reduce unnecessary UI fallbacks, faster API recovery detection",
                affected_parameters=['api_health_check_interval', 'fallback_threshold']
            )
            plan.metrics_evidence = {
                'baseline_ui_fallbacks': baseline_ui,
                'current_ui_fallbacks': current_ui
            }
            plan.estimated_impact = f"UI fallbacks: {current_ui} → {int(current_ui * 0.7)}"
            return plan
        
        return None
    
    def _analyze_control_signal_patterns(self, decision_log: List[dict]) -> Optional[ChangePlan]:
        """Анализ эффективности control signals"""
        if len(decision_log) < 5:
            return None
        
        # Подсчитать частоту активации сигналов
        activations = [d for d in decision_log if d.get('action') == 'signal_activated']
        
        if len(activations) >= 3:
            # Частые активации → нужно настроить TTL
            plan = ChangePlan(
                description="Optimize control signal TTL durations",
                scope=ChangePlanScope.PARAMETER,
                justification=f"{len(activations)} signal activations in recent history. "
                              f"May need TTL adjustment to prevent signal churn.",
                expected_gain="Reduce signal overhead, stabilize control loop",
                affected_parameters=['signal_ttl_short', 'signal_ttl_medium', 'signal_ttl_long']
            )
            plan.metrics_evidence = {
                'total_decisions': len(decision_log),
                'signal_activations': len(activations)
            }
            return plan
        
        return None


class PlanRegistry:
    """
    In-memory registry для хранения change plans
    
    ULTRA-BLACK COMPLIANCE:
    - In-memory only
    - No side effects
    - Optional persistence to .baseline/
    """
    
    def __init__(self):
        self.plans: List[ChangePlan] = []
        self.logger = logging.getLogger('PlanRegistry')
    
    def add_plan(self, plan: ChangePlan):
        """Добавить план в registry"""
        self.plans.append(plan)
        self.logger.info(f"✓ Plan registered: {plan.id} ({plan.scope.value})")
    
    def get_plans_by_status(self, status: str) -> List[ChangePlan]:
        """Получить планы по статусу"""
        return [p for p in self.plans if p.status == status]
    
    def get_plans_by_risk(self, risk_level: ChangePlanRisk) -> List[ChangePlan]:
        """Получить планы по уровню риска"""
        return [p for p in self.plans if p.risk_level == risk_level]
    
    def get_all_plans(self) -> List[ChangePlan]:
        """Получить все планы"""
        return self.plans
    
    def save_to_file(self, filepath: str):
        """Сохранить планы в JSON"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_plans': len(self.plans),
                'plans': [p.to_dict() for p in self.plans]
            }
            
            Path(filepath).parent.mkdir(exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"✓ Plans saved: {filepath}")
        except Exception as e:
            self.logger.warning(f"Failed to save plans: {e}")


class PlanReporter:
    """
    Генератор отчётов по change plans
    
    JSON + human-readable форматы
    """
    
    def __init__(self, registry: PlanRegistry):
        self.registry = registry
        self.logger = logging.getLogger('PlanReporter')
    
    def generate_report(self) -> dict:
        """Сгенерировать JSON отчёт"""
        all_plans = self.registry.get_all_plans()
        
        return {
            'meta_planning': {
                'autonomy_level': 'LEVEL_2_META_PLANNING',
                'total_plans': len(all_plans),
                'by_status': self._count_by_status(all_plans),
                'by_risk': self._count_by_risk(all_plans),
                'by_scope': self._count_by_scope(all_plans),
                'plans': [p.to_dict() for p in all_plans]
            }
        }
    
    def _count_by_status(self, plans: List[ChangePlan]) -> dict:
        """Подсчитать планы по статусу"""
        statuses = ['proposed', 'approved', 'rejected', 'applied']
        return {status: len([p for p in plans if p.status == status]) for status in statuses}
    
    def _count_by_risk(self, plans: List[ChangePlan]) -> dict:
        """Подсчитать планы по риску"""
        return {
            'safe': len(self.registry.get_plans_by_risk(ChangePlanRisk.SAFE)),
            'review': len(self.registry.get_plans_by_risk(ChangePlanRisk.REVIEW)),
            'forbidden': len(self.registry.get_plans_by_risk(ChangePlanRisk.FORBIDDEN))
        }
    
    def _count_by_scope(self, plans: List[ChangePlan]) -> dict:
        """Подсчитать планы по scope"""
        return {
            'parameter': len([p for p in plans if p.scope == ChangePlanScope.PARAMETER]),
            'logic': len([p for p in plans if p.scope == ChangePlanScope.LOGIC]),
            'architecture': len([p for p in plans if p.scope == ChangePlanScope.ARCHITECTURE])
        }
    
    def format_human_readable(self, plans: List[ChangePlan]) -> str:
        """Человекочитаемый формат"""
        if not plans:
            return "\n✅ No change plans proposed\n"
        
        output = "\n"
        output += "╔" + "═" * 62 + "╗\n"
        output += "║" + " " * 15 + "META-PLANNING PROPOSALS" + " " * 24 + "║\n"
        output += "╠" + "═" * 62 + "╣\n"
        output += "║" + " " * 62 + "║\n"
        output += f"║  Total Plans: {len(plans):2d}" + " " * 45 + "║\n"
        output += "║" + " " * 62 + "║\n"
        
        # Группировка по риску
        safe = [p for p in plans if p.risk_level == ChangePlanRisk.SAFE]
        review = [p for p in plans if p.risk_level == ChangePlanRisk.REVIEW]
        forbidden = [p for p in plans if p.risk_level == ChangePlanRisk.FORBIDDEN]
        
        if safe:
            output += "╠" + "═" * 62 + "╣\n"
            output += "║  🟢 SAFE (LEVEL A - Parameter Changes)" + " " * 20 + "║\n"
            output += "╠" + "═" * 62 + "╣\n"
            for plan in safe:
                output += "║" + " " * 62 + "║\n"
                desc_lines = self._wrap_text(plan.description, 58)
                for line in desc_lines:
                    output += f"║  {line:<60}║\n"
                output += f"║    Impact: {plan.expected_gain[:53]:<53}║\n"
                params = ", ".join(plan.affected_parameters[:3])
                output += f"║    Params: {params[:53]:<53}║\n"
        
        if review:
            output += "╠" + "═" * 62 + "╣\n"
            output += "║  🟡 REVIEW (LEVEL B - Logic Changes)" + " " * 22 + "║\n"
            output += "╠" + "═" * 62 + "╣\n"
            for plan in review:
                output += "║" + " " * 62 + "║\n"
                desc_lines = self._wrap_text(plan.description, 58)
                for line in desc_lines:
                    output += f"║  {line:<60}║\n"
                output += f"║    ⚠️  Requires human approval" + " " * 33 + "║\n"
        
        if forbidden:
            output += "╠" + "═" * 62 + "╣\n"
            output += "║  🔴 FORBIDDEN (LEVEL C - Architecture)" + " " * 20 + "║\n"
            output += "╠" + "═" * 62 + "╣\n"
            output += "║    (No plans - architecture changes not allowed)" + " " * 12 + "║\n"
        
        output += "║" + " " * 62 + "║\n"
        output += "╚" + "═" * 62 + "╝\n"
        
        return output
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Перенос текста по ширине"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines or [""]
