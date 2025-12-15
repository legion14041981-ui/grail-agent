#!/usr/bin/env python3
"""
Overlord Executor - Safe Parameter Application
Version: 1.0.0 (Level 2.5 Autonomy)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

OVERLORD-SUPREME: Safe Execution Layer

Autonomy Level: LEVEL 2.5 (Sanctioned Execution)
- Apply approved SAFE plans
- Parametric substitution (JSON only)
- NO code generation
- Rollback capability

Restrictions:
- JSON config updates ONLY
- NO code modification
- Whitelisted parameters
- Range validation
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any

try:
    from overlord_approver import ApprovedChangePlan
except ImportError:
    ApprovedChangePlan = None


class ParameterWhitelist:
    """
    Whitelist разрешённых параметров
    
    ULTRA-BLACK COMPLIANCE:
    - Только перечисленные параметры
    - С указанием диапазона
    - С указанием типа
    """
    
    ALLOWED_PARAMETERS = {
        # Trading parameters
        'confidence_threshold': {
            'type': float,
            'min': 0.60,
            'max': 0.90,
            'description': 'Confidence threshold for predictions'
        },
        'max_predictions': {
            'type': int,
            'min': 5,
            'max': 200,
            'description': 'Maximum number of predictions per session'
        },
        
        # Control signal TTL
        'ttl_short': {
            'type': int,
            'min': 1800,  # 30 min
            'max': 3600,  # 1 hour
            'description': 'TTL for short-lived control signals (seconds)'
        },
        'ttl_medium': {
            'type': int,
            'min': 3600,  # 1 hour
            'max': 7200,  # 2 hours
            'description': 'TTL for medium-lived control signals (seconds)'
        },
        'ttl_long': {
            'type': int,
            'min': 7200,  # 2 hours
            'max': 14400, # 4 hours
            'description': 'TTL for long-lived control signals (seconds)'
        },
        
        # API retry
        'api_retry_count': {
            'type': int,
            'min': 1,
            'max': 5,
            'description': 'Number of API retry attempts'
        },
        'api_timeout_ms': {
            'type': int,
            'min': 5000,   # 5s
            'max': 30000,  # 30s
            'description': 'API request timeout (milliseconds)'
        },
        
        # Fallback thresholds
        'ui_fallback_threshold': {
            'type': int,
            'min': 3,
            'max': 10,
            'description': 'Max UI fallbacks before alert'
        }
    }
    
    @classmethod
    def is_allowed(cls, parameter_name: str) -> bool:
        """Проверить, разрешён ли параметр"""
        return parameter_name in cls.ALLOWED_PARAMETERS
    
    @classmethod
    def get_spec(cls, parameter_name: str) -> Optional[Dict]:
        """Получить спецификацию параметра"""
        return cls.ALLOWED_PARAMETERS.get(parameter_name)


class ConfigValidator:
    """
    Валидация параметров перед применением
    
    ULTRA-BLACK COMPLIANCE:
    - Type checking
    - Range validation
    - Whitelist enforcement
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ConfigValidator')
    
    def validate(
        self,
        parameter_name: str,
        value: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Валидировать параметр
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: Параметр в whitelist?
        if not ParameterWhitelist.is_allowed(parameter_name):
            return False, f"Parameter '{parameter_name}' not in whitelist"
        
        # Check 2: Получить spec
        spec = ParameterWhitelist.get_spec(parameter_name)
        if not spec:
            return False, f"No spec found for '{parameter_name}'"
        
        # Check 3: Type
        expected_type = spec['type']
        if not isinstance(value, expected_type):
            return False, f"Expected {expected_type.__name__}, got {type(value).__name__}"
        
        # Check 4: Range
        if 'min' in spec and value < spec['min']:
            return False, f"Value {value} below minimum {spec['min']}"
        
        if 'max' in spec and value > spec['max']:
            return False, f"Value {value} above maximum {spec['max']}"
        
        # Valid
        return True, None
    
    def validate_batch(
        self,
        parameters: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Валидировать набор параметров
        
        Returns:
            (all_valid, error_messages)
        """
        errors = []
        
        for param_name, value in parameters.items():
            is_valid, error = self.validate(param_name, value)
            if not is_valid:
                errors.append(f"{param_name}: {error}")
        
        return len(errors) == 0, errors


class RollbackManager:
    """
    Управление rollback'ами
    
    ULTRA-BLACK COMPLIANCE:
    - Сохраняет backup перед изменением
    - Позволяет откатить изменения
    """
    
    def __init__(self, backup_dir: str = ".baseline/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('RollbackManager')
    
    def create_backup(
        self,
        config_file: Path,
        plan_id: str
    ) -> Optional[Path]:
        """
        Создать backup конфига
        
        Returns:
            Path to backup file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_backup_{plan_id}_{timestamp}.json"
            
            shutil.copy2(config_file, backup_file)
            
            self.logger.info(f"✓ Backup created: {backup_file}")
            return backup_file
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create backup: {e}")
            return None
    
    def rollback(
        self,
        backup_file: Path,
        config_file: Path
    ) -> bool:
        """
        Откатить изменения
        
        Returns:
            True if successful
        """
        try:
            if not backup_file.exists():
                self.logger.error(f"❌ Backup file not found: {backup_file}")
                return False
            
            shutil.copy2(backup_file, config_file)
            
            self.logger.info(f"✓ Rollback successful: {config_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {e}")
            return False


class SafeExecutor:
    """
    Безопасное применение SAFE планов
    
    LEVEL 2.5 AUTONOMY: Sanctioned Parameter Execution
    
    ULTRA-BLACK COMPLIANCE:
    - Только JSON config updates
    - Нет генерации кода
    - Нет eval/exec
    - Rollback capability
    """
    
    def __init__(
        self,
        config_file: str = "config/parameters.json",
        backup_dir: str = ".baseline/backups"
    ):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.validator = ConfigValidator()
        self.rollback_manager = RollbackManager(backup_dir)
        self.logger = logging.getLogger('SafeExecutor')
        
        # Инициализировать config file если не существует
        self._init_config_if_missing()
    
    def _init_config_if_missing(self):
        """
        Создать дефолтный config если не существует
        """
        if not self.config_file.exists():
            default_config = {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'parameters': {
                    'confidence_threshold': 0.70,
                    'max_predictions': 20,
                    'ttl_short': 1800,
                    'ttl_medium': 3600,
                    'ttl_long': 7200,
                    'api_retry_count': 3,
                    'api_timeout_ms': 10000,
                    'ui_fallback_threshold': 5
                },
                'modifications': []
            }
            
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                self.logger.info(f"✓ Default config created: {self.config_file}")
            except Exception as e:
                self.logger.error(f"Failed to create default config: {e}")
    
    def apply(
        self,
        approved_plan: ApprovedChangePlan
    ) -> tuple[bool, Optional[str]]:
        """
        Применить одобренный план
        
        Returns:
            (success, error_message)
        """
        # Validation 1: Проверить валидность одобрения
        if not approved_plan.is_valid():
            return False, f"Approval not valid: {approved_plan.status}"
        
        # Validation 2: Проверить целостность
        if not approved_plan.verify_integrity():
            return False, "Integrity check failed: plan was modified after approval"
        
        # Validation 3: Проверить scope
        if approved_plan.plan.scope.value != "parameter":
            return False, f"Invalid scope: {approved_plan.plan.scope.value} (expected: parameter)"
        
        # Validation 4: Проверить risk
        if approved_plan.plan.risk_level.value != "safe":
            return False, f"Invalid risk: {approved_plan.plan.risk_level.value} (expected: safe)"
        
        self.logger.info(f"🎯 Applying SAFE plan: {approved_plan.plan_id}")
        self.logger.info(f"   Approved by: {approved_plan.approved_by}")
        self.logger.info(f"   Plan: {approved_plan.plan.description}")
        
        # Создать backup
        backup_file = self.rollback_manager.create_backup(
            self.config_file,
            approved_plan.plan_id
        )
        
        if not backup_file:
            return False, "Failed to create backup"
        
        try:
            # Загрузить текущий config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Получить параметры из плана
            # (в реальности нужно парсить из plan.affected_parameters)
            # Для демо: предположим, что параметры в plan.metrics_evidence
            parameters_to_change = self._extract_parameters(approved_plan.plan)
            
            if not parameters_to_change:
                return False, "No parameters found in plan"
            
            # Валидировать параметры
            all_valid, errors = self.validator.validate_batch(parameters_to_change)
            
            if not all_valid:
                self.logger.error(f"❌ Validation failed:")
                for error in errors:
                    self.logger.error(f"   - {error}")
                return False, f"Validation failed: {'; '.join(errors)}"
            
            # Применить изменения
            old_values = {}
            for param_name, new_value in parameters_to_change.items():
                old_value = config['parameters'].get(param_name)
                old_values[param_name] = old_value
                config['parameters'][param_name] = new_value
                
                self.logger.info(
                    f"   {param_name}: {old_value} → {new_value}"
                )
            
            # Добавить запись об изменении
            modification = {
                'plan_id': approved_plan.plan_id,
                'applied_at': datetime.now().isoformat(),
                'approved_by': approved_plan.approved_by,
                'changes': parameters_to_change,
                'old_values': old_values,
                'backup_file': str(backup_file),
                'description': approved_plan.plan.description
            }
            config['modifications'].append(modification)
            
            # Сохранить config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Отметить как applied
            approved_plan.mark_applied()
            
            self.logger.info(
                f"✅ SAFE plan applied successfully: {approved_plan.plan_id}"
            )
            
            return True, None
        
        except Exception as e:
            self.logger.error(f"❌ Failed to apply plan: {e}")
            
            # Попытаться откатить
            if backup_file:
                self.logger.info("🔄 Attempting rollback...")
                if self.rollback_manager.rollback(backup_file, self.config_file):
                    self.logger.info("✓ Rollback successful")
                else:
                    self.logger.error("❌ Rollback failed")
            
            return False, str(e)
    
    def _extract_parameters(self, plan) -> Dict[str, Any]:
        """
        Извлечь параметры из плана
        
        В реальности нужно парсить из plan.description или
        plan.metrics_evidence
        
        Для демо: возвращаем примерные значения
        """
        # TODO: Реальная логика extraction
        # Сейчас просто пример
        
        if 'confidence' in plan.description.lower():
            return {'confidence_threshold': 0.75}
        
        if 'retry' in plan.description.lower():
            return {'api_retry_count': 5}
        
        if 'ttl' in plan.description.lower():
            return {'ttl_medium': 4500}
        
        # По умолчанию: пустой dict
        return {}
    
    def get_current_config(self) -> Optional[Dict]:
        """
        Получить текущий config
        """
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return None
