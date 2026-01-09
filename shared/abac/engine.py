"""
ABAC (Attribute-Based Access Control) Engine

Implements a custom Specification Pattern for access control.
No external libraries - pure Python implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import User
    from apps.catalog.models import Asset


@dataclass
class AccessContext:
    """
    Context object containing all attributes needed for policy evaluation.
    """
    user: 'User'
    resource: 'Asset'
    action: str = 'INVEST'  # Default action

    @property
    def user_tenant_id(self) -> Optional[int]:
        return self.user.tenant_id if self.user.tenant else None

    @property
    def resource_tenant_id(self) -> Optional[int]:
        return self.resource.tenant_id if hasattr(self.resource, 'tenant_id') else None


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    allowed: bool
    violations: List[str] = field(default_factory=list)
    
    def add_violation(self, message: str) -> None:
        self.violations.append(message)
        self.allowed = False


class AccessRule(Protocol):
    """
    Protocol for access rules (Specification Pattern).
    
    Each rule evaluates a specific access control requirement.
    """
    
    def evaluate(self, context: AccessContext) -> bool:
        """
        Evaluate the rule against the given context.
        
        Returns:
            True if access is allowed, False otherwise.
        """
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the rule."""
        ...

    def get_violation_message(self, context: AccessContext) -> str:
        """Message to display when the rule is violated."""
        ...


class TenantIsolationRule:
    """
    Rule 1: Tenant Isolation
    
    Ensures users can only access resources within their tenant.
    user.tenant_id == resource.tenant_id
    """
    
    @property
    def name(self) -> str:
        return "TenantIsolation"

    def evaluate(self, context: AccessContext) -> bool:
        return context.user_tenant_id == context.resource_tenant_id

    def get_violation_message(self, context: AccessContext) -> str:
        return "Access denied: Resource belongs to a different tenant"


class RiskCheckRule:
    """
    Rule 2: Risk Tolerance Check
    
    Ensures users only invest in assets matching their risk tolerance.
    user.risk_tolerance >= asset.risk_level
    """
    
    @property
    def name(self) -> str:
        return "RiskCheck"

    def evaluate(self, context: AccessContext) -> bool:
        return context.user.risk_tolerance >= context.resource.risk_level

    def get_violation_message(self, context: AccessContext) -> str:
        return (
            f"Risk check failed: Your risk tolerance ({context.user.risk_tolerance}) "
            f"is below the asset's risk level ({context.resource.risk_level})"
        )


class AccreditationRule:
    """
    Rule 3: Accreditation Check
    
    Ensures only accredited investors can access VIP assets.
    If asset.accreditation_required, then user.is_accredited must be True
    """
    
    @property
    def name(self) -> str:
        return "Accreditation"

    def evaluate(self, context: AccessContext) -> bool:
        if not context.resource.accreditation_required:
            return True  # No accreditation needed
        return context.user.is_accredited

    def get_violation_message(self, context: AccessContext) -> str:
        return "Accreditation required: This asset is only available to accredited investors"


class PolicyEngine:
    """
    The main Policy Engine that orchestrates all access rules.
    
    Usage:
        engine = PolicyEngine()
        context = AccessContext(user=user, resource=asset)
        result = engine.check_all(context)
        if not result.allowed:
            raise PolicyViolationError(result.violations)
    """

    def __init__(self, rules: Optional[List[AccessRule]] = None):
        """
        Initialize with default rules or custom rules.
        
        Args:
            rules: Custom list of rules. If None, uses default rules.
        """
        self.rules: List[AccessRule] = rules or [
            TenantIsolationRule(),
            RiskCheckRule(),
            AccreditationRule(),
        ]

    def check(self, rule: AccessRule, context: AccessContext) -> bool:
        """Check a single rule."""
        return rule.evaluate(context)

    def check_all(self, context: AccessContext) -> PolicyResult:
        """
        Check all rules and return aggregated result.
        
        Returns:
            PolicyResult with allowed=True if all rules pass,
            or allowed=False with list of violations.
        """
        result = PolicyResult(allowed=True)

        for rule in self.rules:
            if not rule.evaluate(context):
                result.add_violation(rule.get_violation_message(context))

        return result

    def add_rule(self, rule: AccessRule) -> None:
        """Add a custom rule to the engine."""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False
