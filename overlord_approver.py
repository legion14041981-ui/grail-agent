#!/usr/bin/env python3
"""
Overlord Approver - Plan Approval Workflow
Version: 1.0.0 (Level 2.5 Autonomy)
Author: OVERLORD-SUPREME / Legion Framework
Date: 2025-12-15

OVERLORD-SUPREME: Sanctioned Execution Layer

Autonomy Level: LEVEL 2.5 (Sanctioned Execution)
- Human approval workflow
- SAFE plan approval only
- Checksum validation
- TTL enforcement

Restrictions:
- NO auto-approval
- NO REVIEW/FORBIDDEN approval
- Human decision mandatory
- Approval expires (TTL)
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

try:
    from overlord_metaplanner import ChangePlan, ChangePlanScope, ChangePlanRisk
except ImportError:
    ChangePlan = None
    ChangePlanScope = None
    ChangePlanRisk = None


class ApprovedChangePlan:
    """
    Одобренный план изменений
    
    ULTRA-BLACK COMPLIANCE:
    - Только SAFE планы (PARAMETER scope)
    - Checksum для проверки целостности
    - TTL для автоматического истечения
    - Human approval обязателен
    """
    
    def __init__(
        self,
        plan: 'ChangePlan',
        approved_by: str,
        approval_reason: str,
        ttl_hours: int = 48
    ):
        # Проверка: только SAFE планы
        if plan.risk_level.value != "safe":
            raise ValueError(f"Cannot approve {plan.risk_level.value} plan. Only SAFE plans allowed.")
        
        # Проверка: только PARAMETER scope
        if plan.scope.value != "parameter":
            raise ValueError(f"Cannot approve {plan.scope.value} plan. Only PARAMETER scope allowed.")
        
        self.plan_id = plan.id
        self.plan = plan
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=ttl_hours)
        self.approval_reason = approval_reason
        
        # Checksum для проверки целостности
        self.checksum = self._calculate_checksum(plan)
        
        # Статус
        self.status = "approved"  # approved / applied / expired / revoked
        self.applied_at = None
        self.revoked_at = None
        self.revoke_reason = None
    
    def _calculate_checksum(self, plan: 'ChangePlan') -> str:
        """
        Вычислить checksum плана (SHA256)
        
        Используется для проверки, что план не изменился
        после одобрения
        """
        plan_content = f"{plan.id}|{plan.description}|{plan.scope.value}|" \
                       f"{plan.affected_parameters}|{plan.created_at.isoformat()}"
        return hashlib.sha256(plan_content.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """
        Проверить валидность одобрения
        
        Returns:
            True если одобрение активно и не истекло
        """
        if self.status != "approved":
            return False
        
        if datetime.now() > self.expires_at:
            self.status = "expired"
            return False
        
        return True
    
    def verify_integrity(self) -> bool:
        """
        Проверить целостность плана
        
        Returns:
            True если checksum совпадает
        """
        current_checksum = self._calculate_checksum(self.plan)
        return current_checksum == self.checksum
    
    def revoke(self, reason: str):
        """
        Отозвать одобрение
        
        Args:
            reason: Причина отзыва
        """
        self.status = "revoked"
        self.revoked_at = datetime.now()
        self.revoke_reason = reason
    
    def mark_applied(self):
        """
        Отметить как применённый
        """
        self.status = "applied"
        self.applied_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        Сериализация в JSON
        """
        return {
            'plan_id': self.plan_id,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'approval_reason': self.approval_reason,
            'checksum': self.checksum,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoke_reason': self.revoke_reason,
            'plan': self.plan.to_dict()
        }


class PlanApprover:
    """
    Workflow для одобрения планов человеком
    
    LEVEL 2.5 AUTONOMY:
    - Human approval required
    - SAFE plans only
    - Transparent process
    - Audit trail
    """
    
    def __init__(self, approval_dir: str = ".baseline/approvals"):
        self.approval_dir = Path(approval_dir)
        self.approval_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('PlanApprover')
    
    def request_approval(
        self,
        plan: 'ChangePlan',
        requester: str = "overlord"
    ) -> dict:
        """
        Запросить одобрение плана
        
        Args:
            plan: План для одобрения
            requester: Кто запросил (для аудита)
        
        Returns:
            Approval request metadata
        """
        # Валидация: только SAFE планы
        if plan.risk_level.value != "safe":
            self.logger.warning(
                f"⚠️  Cannot request approval for {plan.risk_level.value} plan: {plan.id}"
            )
            return {
                'status': 'rejected',
                'reason': f'Only SAFE plans can be approved. This is {plan.risk_level.value}.'
            }
        
        # Создать запрос на одобрение
        request = {
            'request_id': f"req_{plan.id}",
            'plan_id': plan.id,
            'requested_by': requester,
            'requested_at': datetime.now().isoformat(),
            'status': 'pending',
            'plan_summary': {
                'description': plan.description,
                'scope': plan.scope.value,
                'risk': plan.risk_level.value,
                'affected_parameters': plan.affected_parameters,
                'expected_gain': plan.expected_gain,
                'justification': plan.justification
            }
        }
        
        # Сохранить запрос
        request_file = self.approval_dir / f"request_{plan.id}.json"
        try:
            with open(request_file, 'w') as f:
                json.dump(request, f, indent=2)
            
            self.logger.info(f"✓ Approval request created: {plan.id}")
            self.logger.info(f"   Plan: {plan.description}")
            self.logger.info(f"   Impact: {plan.expected_gain}")
            self.logger.info(f"   File: {request_file}")
            
            return {
                'status': 'pending',
                'request_id': request['request_id'],
                'request_file': str(request_file)
            }
        
        except Exception as e:
            self.logger.error(f"Failed to create approval request: {e}")
            return {
                'status': 'error',
                'reason': str(e)
            }
    
    def approve(
        self,
        plan: 'ChangePlan',
        approved_by: str,
        reason: str,
        ttl_hours: int = 48
    ) -> Optional[ApprovedChangePlan]:
        """
        Одобрить план (HUMAN ACTION)
        
        Args:
            plan: План для одобрения
            approved_by: Кто одобрил (email/username)
            reason: Причина одобрения
            ttl_hours: Срок действия одобрения (часы)
        
        Returns:
            ApprovedChangePlan если успешно, None если ошибка
        """
        try:
            # Создать одобренный план
            approved = ApprovedChangePlan(
                plan=plan,
                approved_by=approved_by,
                approval_reason=reason,
                ttl_hours=ttl_hours
            )
            
            # Сохранить одобрение
            approval_file = self.approval_dir / f"approval_{plan.id}.json"
            with open(approval_file, 'w') as f:
                json.dump(approved.to_dict(), f, indent=2)
            
            self.logger.info(f"✅ Plan APPROVED: {plan.id}")
            self.logger.info(f"   By: {approved_by}")
            self.logger.info(f"   Reason: {reason}")
            self.logger.info(f"   Expires: {approved.expires_at.isoformat()}")
            self.logger.info(f"   File: {approval_file}")
            
            return approved
        
        except ValueError as e:
            self.logger.error(f"❌ Approval failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Approval error: {e}")
            return None
    
    def reject(
        self,
        plan: 'ChangePlan',
        rejected_by: str,
        reason: str
    ) -> dict:
        """
        Отклонить план (HUMAN ACTION)
        
        Args:
            plan: План для отклонения
            rejected_by: Кто отклонил
            reason: Причина отклонения
        
        Returns:
            Rejection metadata
        """
        rejection = {
            'plan_id': plan.id,
            'rejected_by': rejected_by,
            'rejected_at': datetime.now().isoformat(),
            'reason': reason,
            'plan_summary': plan.description
        }
        
        # Сохранить отклонение
        rejection_file = self.approval_dir / f"rejection_{plan.id}.json"
        try:
            with open(rejection_file, 'w') as f:
                json.dump(rejection, f, indent=2)
            
            self.logger.info(f"❌ Plan REJECTED: {plan.id}")
            self.logger.info(f"   By: {rejected_by}")
            self.logger.info(f"   Reason: {reason}")
            
            return {
                'status': 'rejected',
                'rejection_file': str(rejection_file)
            }
        
        except Exception as e:
            self.logger.error(f"Failed to save rejection: {e}")
            return {
                'status': 'error',
                'reason': str(e)
            }


class ApprovalRegistry:
    """
    Реестр одобренных планов
    
    In-memory + persistent storage
    """
    
    def __init__(self, approval_dir: str = ".baseline/approvals"):
        self.approval_dir = Path(approval_dir)
        self.approval_dir.mkdir(parents=True, exist_ok=True)
        self.approved_plans: List[ApprovedChangePlan] = []
        self.logger = logging.getLogger('ApprovalRegistry')
        
        # Загрузить существующие одобрения
        self._load_existing_approvals()
    
    def _load_existing_approvals(self):
        """
        Загрузить существующие одобрения из файлов
        """
        try:
            approval_files = self.approval_dir.glob("approval_*.json")
            
            for file in approval_files:
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                    
                    # Проверить статус
                    if data['status'] in ['approved', 'applied']:
                        # Восстановить из JSON (упрощённая версия)
                        # В реальности нужно полное восстановление ChangePlan
                        self.logger.debug(f"Loaded approval: {data['plan_id']}")
                
                except Exception as e:
                    self.logger.warning(f"Failed to load {file}: {e}")
            
            self.logger.info(f"✓ Loaded {len(self.approved_plans)} existing approvals")
        
        except Exception as e:
            self.logger.warning(f"Failed to load approvals: {e}")
    
    def add(self, approved_plan: ApprovedChangePlan):
        """
        Добавить одобренный план в реестр
        """
        self.approved_plans.append(approved_plan)
        self.logger.info(f"✓ Added to registry: {approved_plan.plan_id}")
    
    def get_valid_approvals(self) -> List[ApprovedChangePlan]:
        """
        Получить список валидных одобрений
        
        Returns:
            List of ApprovedChangePlan with status='approved' and not expired
        """
        valid = []
        
        for approval in self.approved_plans:
            if approval.is_valid():
                # Дополнительная проверка целостности
                if approval.verify_integrity():
                    valid.append(approval)
                else:
                    self.logger.warning(
                        f"⚠️  Integrity check failed: {approval.plan_id}"
                    )
        
        return valid
    
    def get_by_plan_id(self, plan_id: str) -> Optional[ApprovedChangePlan]:
        """
        Получить одобрение по ID плана
        """
        for approval in self.approved_plans:
            if approval.plan_id == plan_id:
                return approval
        return None
    
    def cleanup_expired(self):
        """
        Удалить истёкшие одобрения
        """
        expired = [a for a in self.approved_plans if not a.is_valid() and a.status == "expired"]
        
        for approval in expired:
            self.logger.info(f"⏰ Cleaning expired approval: {approval.plan_id}")
            self.approved_plans.remove(approval)
        
        return len(expired)
