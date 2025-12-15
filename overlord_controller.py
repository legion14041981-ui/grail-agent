#!/usr/bin/env python3
"""
Overlord Controller - Control Signals Framework
Version: 1.1.0 (Level 1 + Level 2 Autonomy)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15
Updated: Integrated MetaPlanner (Level 2)

Autonomy Level: LEVEL 1 (Sanctioned)
- Execution guards
- Mode downgrade
- Parameter limits
- Early exit

Autonomy Level: LEVEL 2 (Meta-Planning)
- Change proposal generation
- Risk classification
- Optimization planning
- Human approval required

Restrictions:
- No code changes
- No architecture changes
- Reversible only
- TTL-limited
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from overlord_sentinel import RiskAttractor, RiskLevel, BaselineCollector, RiskSentinel

# STEP 5: Meta-Planning Layer (Level 2 Autonomy)
try:
    from overlord_metaplanner import MetaPlanner, PlanRegistry, ChangePlan
    META_PLANNER_AVAILABLE = True
except ImportError:
    META_PLANNER_AVAILABLE = False
    MetaPlanner = None
    PlanRegistry = None
    ChangePlan = None


class ControlSignalType(Enum):
    """Типы управляющих сигналов Overlord"""
    
    # LEVEL 0: Только наблюдение
    READ_ONLY = "read_only"              # Нет действий
    LOG_ONLY = "log_only"                # Только логирование
    
    # LEVEL 1: Мягкие ограничения
    SOFT_LIMIT = "soft_limit"            # Предупреждение + продолжение
    EXECUTION_GUARD = "execution_guard"  # Проверка перед действием
    
    # LEVEL 1: Жёсткие ограничения
    HARD_LIMIT = "hard_limit"            # Блокировка операции
    MODE_DOWNGRADE = "mode_downgrade"    # Понижение режима (live→demo)
    EARLY_EXIT = "early_exit"            # Завершение с объяснением


class ControlSignal:
    """
    Управляющий сигнал Overlord
    
    Санкционированное влияние на execution БЕЗ изменения кода
    """
    
    def __init__(
        self,
        signal_type: ControlSignalType,
        attractor: RiskAttractor,
        reason: str,
        action: str,
        ttl_seconds: int = 3600,  # 1 час по умолчанию
        reversible: bool = True
    ):
        self.id = f"sig_{int(time.time())}_{random.randint(1000, 9999)}"
        self.signal_type = signal_type
        self.attractor = attractor
        self.reason = reason
        self.action = action
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.reversible = reversible
        self.active = True
    
    def is_expired(self) -> bool:
        """Проверить истечение срока действия"""
        return datetime.now() > self.expires_at
    
    def is_active(self) -> bool:
        """Проверить активность сигнала"""
        return self.active and not self.is_expired()
    
    def revoke(self):
        """Отменить сигнал (только если reversible)"""
        if self.reversible:
            self.active = False
    
    def to_dict(self) -> dict:
        """Сериализация для логирования"""
        return {
            'id': self.id,
            'type': self.signal_type.value,
            'attractor': self.attractor.value,
            'reason': self.reason,
            'action': self.action,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'reversible': self.reversible,
            'active': self.active
        }


class ExecutionControls:
    """
    Параметры execution, которые Overlord может контролировать
    
    РАЗРЕШЕНО:
    - Режимы выполнения
    - Пороговые значения
    - Включение/выключение компонентов
    - Ранний выход
    
    ЗАПРЕЩЕНО:
    - Изменение кода
    - Изменение архитектуры
    - Изменение baseline
    """
    
    def __init__(self):
        # Режимы
        self.force_demo_mode = False           # Принудительный demo
        self.block_live_mode = False           # Блокировка live
        self.disable_ui_fallback = False       # Запрет UI
        
        # Пороги
        self.confidence_threshold = 0.70       # Базовый порог
        self.max_predictions = None            # Лимит предсказаний
        
        # Компоненты
        self.skip_ml_inference = False         # Пропуск ML
        self.disable_supabase = False          # Отключить DB
        
        # CI controls
        self.ci_early_exit = False             # Ранний выход CI
        self.ci_exit_reason = None             # Причина выхода
    
    def apply_signal(self, signal: ControlSignal):
        """Применить управляющий сигнал"""
        if not signal.is_active():
            return
        
        # HARD_LIMIT: жёсткие блокировки
        if signal.signal_type == ControlSignalType.HARD_LIMIT:
            if signal.attractor == RiskAttractor.DEMO_ONLY_MODE:
                self.force_demo_mode = True
                self.block_live_mode = True
        
        # MODE_DOWNGRADE: понижение режима
        elif signal.signal_type == ControlSignalType.MODE_DOWNGRADE:
            if signal.attractor == RiskAttractor.PLAYWRIGHT_INIT_FAIL:
                self.disable_ui_fallback = True
        
        # EARLY_EXIT: завершение с причиной
        elif signal.signal_type == ControlSignalType.EARLY_EXIT:
            if signal.attractor == RiskAttractor.RUNTIME_SPIKE:
                self.ci_early_exit = True
                self.ci_exit_reason = "Runtime exceeded baseline threshold"
                if self.max_predictions is None or self.max_predictions > 5:
                    self.max_predictions = 5  # Ограничить до 5
        
        # EXECUTION_GUARD: проверки перед действиями
        elif signal.signal_type == ControlSignalType.EXECUTION_GUARD:
            if signal.attractor == RiskAttractor.API_SCORE_DROP:
                # Будет проверяться в execution guard
                pass
    
    def should_exit_early(self) -> Tuple[bool, Optional[str]]:
        """Проверить необходимость раннего выхода"""
        if self.ci_early_exit:
            return True, self.ci_exit_reason
        return False, None


class OverlordController:
    """
    Контроллер Overlord: Metrics → Sentinel → Signals → Guards → MetaPlanner
    
    LEVEL 1 AUTONOMY: Санкционированное влияние
    LEVEL 2 AUTONOMY: Meta-planning (предложения изменений)
    """
    
    def __init__(self, baseline: BaselineCollector, sentinel: RiskSentinel):
        self.baseline = baseline
        self.sentinel = sentinel
        self.active_signals: List[ControlSignal] = []
        self.execution_controls = ExecutionControls()
        self.decision_log = []
        self.logger = logging.getLogger('OverlordController')
        
        # STEP 5: Meta-Planning Layer (Level 2)
        self.meta_planner = None
        self.plan_registry = None
        
        if META_PLANNER_AVAILABLE:
            try:
                self.meta_planner = MetaPlanner(baseline, sentinel)
                self.plan_registry = PlanRegistry()
                self.logger.info("✓ Meta-Planner initialized (Level 2 Autonomy)")
            except Exception as e:
                self.logger.debug(f"⚠️  Meta-Planner init failed (non-critical): {e}")
        else:
            self.logger.debug("⚠️  Meta-Planner not available (overlord_metaplanner.py missing)")
    
    def evaluate_and_apply(self, current_metrics: dict) -> ExecutionControls:
        """
        Полный цикл: оценка → сигналы → применение
        
        Returns:
            ExecutionControls с активными ограничениями
        """
        # 1. Проверить риски через Sentinel
        risk_signals = self.sentinel.check_risks(current_metrics)
        
        # 2. Генерировать control signals
        new_signals = self._generate_control_signals(risk_signals)
        
        # 3. Применить активные сигналы
        self._apply_signals(new_signals)
        
        # 4. Очистить истёкшие
        self._cleanup_expired_signals()
        
        # 5. Логировать решения
        self._log_decisions()
        
        return self.execution_controls
    
    def generate_plans(self, current_metrics: dict) -> List:
        """
        Сгенерировать change plans (ПРЕДЛОЖЕНИЯ изменений)
        
        LEVEL 2 AUTONOMY: Meta-Planning
        - Анализ baseline trends
        - Генерация планов оптимизации
        - Классификация рисков
        
        ULTRA-BLACK COMPLIANCE:
        - Нет авто-применения
        - Только предложения
        - Human approval требуется
        
        Returns:
            List of ChangePlan objects
        """
        if not self.meta_planner or not self.plan_registry:
            self.logger.debug("⚠️  Meta-Planner not available, skipping plan generation")
            return []
        
        try:
            # Анализ + генерация планов
            plans = self.meta_planner.analyze_and_plan(current_metrics, self.decision_log)
            
            # Добавить в registry
            for plan in plans:
                self.plan_registry.add_plan(plan)
            
            if plans:
                self.logger.info(f"🧠 Meta-Planner: {len(plans)} change plans generated")
            
            return plans
        
        except Exception as e:
            self.logger.warning(f"Meta-Planner failed (non-critical): {e}")
            return []
    
    def get_active_plans(self) -> List:
        """
        Получить активные change plans
        
        Returns:
            List of ChangePlan objects with status='proposed'
        """
        if not self.plan_registry:
            return []
        
        return self.plan_registry.get_plans_by_status('proposed')
    
    def _generate_control_signals(self, risk_signals: List[Dict]) -> List[ControlSignal]:
        """Генерировать control signals из risk signals"""
        signals = []
        
        for risk in risk_signals:
            attractor = RiskAttractor(risk['attractor'])
            level = RiskLevel(risk['level'])
            
            # HIGH RISK → жёсткие меры
            if level == RiskLevel.HIGH:
                if attractor == RiskAttractor.DEMO_ONLY_MODE:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.HARD_LIMIT,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Force demo mode, block live trading",
                        ttl_seconds=7200
                    ))
                
                elif attractor == RiskAttractor.SUPABASE_DOWN:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.SOFT_LIMIT,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Continue without Supabase logging",
                        ttl_seconds=1800
                    ))
                
                elif attractor == RiskAttractor.PLAYWRIGHT_INIT_FAIL:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.MODE_DOWNGRADE,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Disable UI fallback, API-only mode",
                        ttl_seconds=3600
                    ))
            
            # MEDIUM RISK → мягкие меры
            elif level == RiskLevel.MEDIUM:
                if attractor == RiskAttractor.API_SCORE_DROP:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.EXECUTION_GUARD,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Verify API health before operations",
                        ttl_seconds=1800
                    ))
                
                elif attractor == RiskAttractor.HIGH_UI_FALLBACK:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.SOFT_LIMIT,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Log excessive UI usage",
                        ttl_seconds=3600
                    ))
                
                elif attractor == RiskAttractor.RUNTIME_SPIKE:
                    signals.append(ControlSignal(
                        signal_type=ControlSignalType.EARLY_EXIT,
                        attractor=attractor,
                        reason=risk['message'],
                        action="Reduce prediction count to 5",
                        ttl_seconds=3600
                    ))
            
            # LOW RISK → только логирование
            else:
                signals.append(ControlSignal(
                    signal_type=ControlSignalType.LOG_ONLY,
                    attractor=attractor,
                    reason=risk['message'],
                    action="Monitor only",
                    ttl_seconds=1800
                ))
        
        return signals
    
    def _apply_signals(self, signals: List[ControlSignal]):
        """Применить новые сигналы"""
        for signal in signals:
            # Проверить, нет ли уже такого сигнала
            existing = self._find_signal(signal.attractor, signal.signal_type)
            
            if existing and existing.is_active():
                # Продлить существующий
                existing.expires_at = signal.expires_at
                self.logger.debug(f"Extended signal: {signal.attractor.value}")
            else:
                # Добавить новый
                self.active_signals.append(signal)
                self.execution_controls.apply_signal(signal)
                
                self.logger.info(
                    f"🎯 CONTROL SIGNAL ACTIVATED: {signal.signal_type.value} "
                    f"for {signal.attractor.value}"
                )
                
                # Записать решение
                self.decision_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'signal_activated',
                    'signal': signal.to_dict()
                })
    
    def _find_signal(self, attractor: RiskAttractor, signal_type: ControlSignalType) -> Optional[ControlSignal]:
        """Найти существующий сигнал"""
        for signal in self.active_signals:
            if signal.attractor == attractor and signal.signal_type == signal_type:
                return signal
        return None
    
    def _cleanup_expired_signals(self):
        """Удалить истёкшие сигналы"""
        expired = [s for s in self.active_signals if s.is_expired()]
        
        for signal in expired:
            self.logger.info(f"⏰ Signal expired: {signal.attractor.value}")
            self.active_signals.remove(signal)
            
            self.decision_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'signal_expired',
                'signal_id': signal.id
            })
    
    def _log_decisions(self):
        """Логировать текущие решения"""
        active_count = len([s for s in self.active_signals if s.is_active()])
        
        if active_count > 0:
            self.logger.info(f"🎯 Active control signals: {active_count}")
            for signal in self.active_signals:
                if signal.is_active():
                    ttl_minutes = (signal.expires_at - datetime.now()).total_seconds() / 60
                    self.logger.info(
                        f"   - {signal.signal_type.value}: {signal.attractor.value} "
                        f"(TTL: {ttl_minutes:.0f}m)"
                    )
    
    def get_active_signals(self) -> List[ControlSignal]:
        """Получить список активных сигналов"""
        return [s for s in self.active_signals if s.is_active()]


class ExecutionGuard:
    """
    Охранник выполнения: проверяет control signals перед операциями
    
    GATE-KEEPER для критических действий
    """
    
    def __init__(self, controller: OverlordController):
        self.controller = controller
        self.logger = logging.getLogger('ExecutionGuard')
    
    def can_enter_live_mode(self) -> Tuple[bool, Optional[str]]:
        """Проверить разрешение live mode"""
        controls = self.controller.execution_controls
        
        if controls.force_demo_mode or controls.block_live_mode:
            return False, "Overlord: Live mode blocked due to DEMO_ONLY_MODE attractor"
        
        return True, None
    
    def can_use_ui_fallback(self) -> Tuple[bool, Optional[str]]:
        """Проверить разрешение UI fallback"""
        controls = self.controller.execution_controls
        
        if controls.disable_ui_fallback:
            return False, "Overlord: UI fallback disabled due to PLAYWRIGHT_INIT_FAIL"
        
        return True, None
    
    def should_skip_ml(self) -> Tuple[bool, Optional[str]]:
        """Проверить необходимость пропуска ML"""
        controls = self.controller.execution_controls
        
        if controls.skip_ml_inference:
            return True, "Overlord: ML inference disabled for performance"
        
        return False, None
    
    def get_prediction_limit(self) -> Optional[int]:
        """Получить лимит предсказаний (если установлен)"""
        controls = self.controller.execution_controls
        return controls.max_predictions
    
    def should_exit_ci(self) -> Tuple[bool, Optional[str]]:
        """Проверить необходимость раннего выхода CI"""
        return self.controller.execution_controls.should_exit_early()
