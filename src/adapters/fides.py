"""Compatibility bridges for the bundled information-flow security pipeline."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import replace
from collections.abc import Mapping, Sequence
from typing import Any

from agent_framework import Content, FunctionInvocationContext, FunctionTool
from agent_framework._middleware import FunctionMiddlewarePipeline
from agent_framework.security import (
    ConfidentialityLabel,
    ContentLabel,
    IntegrityLabel,
    SecureAgentConfig,
)

from core import (
    CanonicalSecurityEvent, Disposition, EventBuilder, ExecutionContext,
    RiskAssessment, RuleRiskEngine, ToolManifest,
)
from core.analyzer import RiskAnalyzer, SemanticAnalysis
from .approval import FidesApprovalAdapter
from eval.runtime import Function, FunctionsRuntime, TaskEnvironment, ToolNotFoundError


class FidesLabelAdapter:
    """A deliberately thin bridge; FIDES remains owned by the upstream package."""

    @staticmethod
    def content_label(event: CanonicalSecurityEvent) -> ContentLabel:
        metadata = {
            "framework": event.framework,
            "session_id": event.session_id,
            **event.principal,
        }
        return ContentLabel(
            integrity=IntegrityLabel(event.integrity.value),
            confidentiality=ConfidentialityLabel(event.confidentiality.value),
            metadata=metadata,
        )


class FidesRuntimeAdapter(FunctionsRuntime):
    """Run local scenario tools through the bundled security middleware.

    This class contains no security decisions. Tool labels and sink constraints are
    accepted as metadata and interpreted exclusively by the upstream middleware.
    """

    def __init__(
        self,
        functions: Sequence[Function] = (),
        *,
        tool_metadata: Mapping[str, Mapping[str, Any]] | None = None,
        security: SecureAgentConfig | None = None,
        risk_engine: RuleRiskEngine | None = None,
        approvals: FidesApprovalAdapter | None = None,
        tool_manifest: ToolManifest | None = None,
        risk_analyzer: RiskAnalyzer | None = None,
        semantic_threshold: float = 0.7,
    ) -> None:
        super().__init__(functions)
        self.security = security or SecureAgentConfig()
        self.risk_engine = risk_engine or RuleRiskEngine()
        self.approvals = approvals or FidesApprovalAdapter()
        self.tool_manifest = tool_manifest
        self.event_builder = EventBuilder(tool_manifest) if tool_manifest is not None else None
        self.risk_analyzer = risk_analyzer
        self.semantic_threshold = semantic_threshold
        self.last_analysis = SemanticAnalysis()
        middleware = [self.security.label_tracker]
        if self.security.policy_enforcer is not None:
            middleware.append(self.security.policy_enforcer)
        self._pipeline = FunctionMiddlewarePipeline(*middleware)
        metadata = dict(tool_manifest.metadata()) if tool_manifest is not None else {}
        metadata.update(tool_metadata or {})
        self._tools = {
            function.name: FunctionTool(
                name=function.name,
                additional_properties=dict(metadata.get(function.name, {})),
                input_model={"type": "object", "additionalProperties": True},
            )
            for function in functions
        }

    async def _observe(
        self,
        content: Any,
        *,
        integrity: IntegrityLabel,
        confidentiality: ConfidentialityLabel,
    ) -> Any:
        source = FunctionTool(
            name="content_source",
            additional_properties={
                "source_integrity": integrity.value,
                "source_confidentiality": confidentiality.value,
                "accepts_untrusted": True,
            },
            input_model={"type": "object", "additionalProperties": False},
        )
        context = FunctionInvocationContext(function=source, arguments={})

        async def read_source(_context: FunctionInvocationContext) -> Any:
            return content

        return await self._pipeline.execute(context, read_source)

    def observe(
        self,
        content: Any,
        *,
        integrity: IntegrityLabel = IntegrityLabel.UNTRUSTED,
        confidentiality: ConfidentialityLabel = ConfidentialityLabel.PUBLIC,
    ) -> Any:
        """Introduce source content through the official label-tracking pipeline."""

        return asyncio.run(
            self._observe(content, integrity=integrity, confidentiality=confidentiality)
        )

    async def _invoke_secured(
        self,
        environment: TaskEnvironment,
        function: Function,
        arguments: Mapping[str, Any],
    ) -> Any:
        context = FunctionInvocationContext(
            function=self._tools[function.name],
            arguments=dict(arguments),
        )

        async def execute(_context: FunctionInvocationContext) -> Any:
            dependencies = {
                name: dependency.extract(environment) for name, dependency in function.dependencies.items()
            }
            result = function.run(**(dict(_context.arguments) | dependencies))
            return await result if inspect.isawaitable(result) else result

        return await self._pipeline.execute(context, execute)

    def run_function(
        self,
        environment: TaskEnvironment,
        function_name: str,
        arguments: Mapping[str, Any],
        *,
        raise_on_error: bool = False,
    ) -> tuple[Any, str | None]:
        function = self.functions.get(function_name)
        if function is None:
            error = f"ToolNotFoundError: {function_name}"
            if raise_on_error:
                raise ToolNotFoundError(error)
            return "", error

        try:
            resolved = {key: self._resolve_nested(environment, value) for key, value in arguments.items()}
            return asyncio.run(self._invoke_secured(environment, function, resolved)), None
        except Exception as exc:
            if raise_on_error:
                raise
            return "", f"{type(exc).__name__}: {exc}"

    def run_event(
        self,
        environment: TaskEnvironment,
        event: CanonicalSecurityEvent,
        *,
        approval_response: Content | None = None,
        approver: Mapping[str, Any] | None = None,
    ) -> tuple[Any, str | None, RiskAssessment]:
        """Risk-route one canonical event before invoking its tool."""

        assessment = self.risk_engine.evaluate(event)
        if assessment.disposition is Disposition.BLOCK:
            return "", f"RiskBlocked: {', '.join(assessment.reasons)}", assessment
        if assessment.disposition in {Disposition.CONFIRM, Disposition.APPROVE}:
            if approval_response is None:
                return self.approvals.request(event, assessment), None, assessment
            result = self.approvals.resolve(
                event, assessment, approval_response, approver=dict(approver or {})
            )
            if not result.approved:
                return "", f"ApprovalDenied: {result.reason}", assessment
        value, error = self.run_function(environment, event.tool_name, event.arguments)
        return value, error, assessment

    def run_tool(
        self,
        environment: TaskEnvironment,
        tool_name: str,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
        *,
        approval_response: Content | None = None,
        approver: Mapping[str, Any] | None = None,
    ) -> tuple[Any, str | None, RiskAssessment]:
        """Unified entry point: context -> event -> risk -> approval -> FIDES."""

        if self.event_builder is None:
            raise RuntimeError("run_tool requires a ToolManifest")
        if self.risk_analyzer is not None:
            self.last_analysis = self.risk_analyzer.analyze(
                task=context.task,
                observations=context.observations,
                tool_name=tool_name,
                arguments=arguments,
            )
            if self.last_analysis.confidence >= self.semantic_threshold:
                context = replace(
                    context,
                    risk_signals=tuple(dict.fromkeys(
                        (*context.risk_signals, *self.last_analysis.signals)
                    )),
                )
        event = self.event_builder.build(tool_name, arguments, context)
        return self.run_event(
            environment, event,
            approval_response=approval_response,
            approver=approver,
        )
