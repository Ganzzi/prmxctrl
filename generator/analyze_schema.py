"""Schema analysis utilities for prmxctrl SDK generation.

This module analyzes parsed schema endpoints to generate metadata
for code generation, including statistics, patterns, and validation.
"""

from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
from dataclasses import dataclass

from .parse_schema import Endpoint, Method, Parameter


@dataclass
class SchemaStats:
    """Statistics about the parsed schema."""

    total_endpoints: int = 0
    total_methods: int = 0
    total_parameters: int = 0
    endpoints_with_children: int = 0
    leaf_endpoints: int = 0
    endpoints_with_path_params: int = 0
    unique_path_param_names: Set[str] = None
    method_counts: Dict[str, int] = None
    parameter_type_counts: Dict[str, int] = None
    format_counts: Dict[str, int] = None

    def __post_init__(self):
        if self.unique_path_param_names is None:
            self.unique_path_param_names = set()
        if self.method_counts is None:
            self.method_counts = {}
        if self.parameter_type_counts is None:
            self.parameter_type_counts = {}
        if self.format_counts is None:
            self.format_counts = {}


@dataclass
class SchemaAnalysis:
    """Complete analysis of parsed schema."""

    stats: SchemaStats
    endpoint_tree: Dict[str, Any]
    common_models: Dict[str, List[Parameter]]
    edge_cases: List[str]
    parameter_patterns: Dict[str, Any]


class SchemaAnalyzer:
    """Analyze parsed schema endpoints for code generation metadata."""

    def analyze(self, endpoints: List[Endpoint]) -> SchemaAnalysis:
        """Analyze endpoints and generate comprehensive metadata.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            SchemaAnalysis with statistics and patterns.
        """
        stats = self._collect_stats(endpoints)
        endpoint_tree = self._build_endpoint_tree(endpoints)
        common_models = self._identify_common_models(endpoints)
        edge_cases = self._detect_edge_cases(endpoints)
        parameter_patterns = self._analyze_parameter_patterns(endpoints)

        return SchemaAnalysis(
            stats=stats,
            endpoint_tree=endpoint_tree,
            common_models=common_models,
            edge_cases=edge_cases,
            parameter_patterns=parameter_patterns,
        )

    def _collect_stats(self, endpoints: List[Endpoint]) -> SchemaStats:
        """Collect comprehensive statistics about the schema.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            SchemaStats with all statistics.
        """
        stats = SchemaStats()

        def traverse_endpoint(endpoint: Endpoint):
            stats.total_endpoints += 1

            if endpoint.children:
                stats.endpoints_with_children += 1
            else:
                stats.leaf_endpoints += 1

            if endpoint.path_params:
                stats.endpoints_with_path_params += 1
                stats.unique_path_param_names.update(endpoint.path_params)

            # Count methods
            for method_name in endpoint.methods:
                stats.total_methods += 1
                stats.method_counts[method_name] = stats.method_counts.get(method_name, 0) + 1

                method = endpoint.methods[method_name]
                stats.total_parameters += len(method.parameters)

                # Count parameter types and formats
                for param in method.parameters:
                    stats.parameter_type_counts[param.type] = (
                        stats.parameter_type_counts.get(param.type, 0) + 1
                    )
                    if param.format:
                        if isinstance(param.format, str):
                            stats.format_counts[param.format] = (
                                stats.format_counts.get(param.format, 0) + 1
                            )
                        elif isinstance(param.format, dict):
                            # Complex format with sub-properties
                            stats.format_counts["complex_format"] = (
                                stats.format_counts.get("complex_format", 0) + 1
                            )

            # Recurse on children
            for child in endpoint.children:
                traverse_endpoint(child)

        for endpoint in endpoints:
            traverse_endpoint(endpoint)

        return stats

    def _build_endpoint_tree(self, endpoints: List[Endpoint]) -> Dict[str, Any]:
        """Build hierarchical tree representation of endpoints.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            Dictionary representing the endpoint hierarchy.
        """

        def endpoint_to_dict(endpoint: Endpoint) -> Dict[str, Any]:
            result = {
                "path": endpoint.path,
                "text": endpoint.text,
                "leaf": endpoint.leaf,
                "path_params": endpoint.path_params,
                "python_path": endpoint.python_path,
                "class_name": endpoint.class_name,
                "methods": list(endpoint.methods.keys()),
                "method_count": len(endpoint.methods),
                "parameter_count": sum(len(m.parameters) for m in endpoint.methods.values()),
            }

            if endpoint.children:
                result["children"] = [endpoint_to_dict(child) for child in endpoint.children]

            return result

        return {
            "root_endpoints": [endpoint_to_dict(ep) for ep in endpoints],
            "total_endpoints": len(endpoints),
        }

    def _identify_common_models(self, endpoints: List[Endpoint]) -> Dict[str, List[Parameter]]:
        """Identify common parameter sets that could be reused as models.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            Dictionary mapping model names to parameter lists.
        """
        # This is a simplified implementation
        # In a full implementation, we'd use clustering or similarity analysis
        common_models = {}

        # For now, just collect all unique parameter sets
        param_sets = defaultdict(list)

        def collect_param_sets(endpoint: Endpoint):
            for method in endpoint.methods.values():
                if len(method.parameters) > 3:  # Only consider methods with multiple params
                    # Create a signature for this parameter set
                    param_sig = tuple(sorted((p.name, p.type) for p in method.parameters))
                    param_sets[param_sig].append((endpoint.path, method.method, method.parameters))

            for child in endpoint.children:
                collect_param_sets(child)

        for endpoint in endpoints:
            collect_param_sets(endpoint)

        # Only keep parameter sets that appear in multiple places
        for i, (param_sig, occurrences) in enumerate(param_sets.items()):
            if len(occurrences) > 1:
                model_name = f"CommonParams{i}"
                # Use the first occurrence's parameters
                common_models[model_name] = occurrences[0][2]

        return common_models

    def _detect_edge_cases(self, endpoints: List[Endpoint]) -> List[str]:
        """Detect edge cases and unusual patterns in the schema.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            List of strings describing edge cases found.
        """
        edge_cases = []

        def check_endpoint(endpoint: Endpoint):
            # Check for dynamic parameters like link[n]
            if "[" in endpoint.path and "]" in endpoint.path:
                edge_cases.append(f"Dynamic parameter pattern in {endpoint.path}")

            # Check for unusual parameter counts
            for method_name, method in endpoint.methods.items():
                if len(method.parameters) > 20:
                    edge_cases.append(
                        f"High parameter count ({len(method.parameters)}) in {endpoint.path} {method_name}"
                    )

                # Check for unusual parameter types
                for param in method.parameters:
                    if param.type not in ["string", "integer", "boolean", "array", "object"]:
                        edge_cases.append(
                            f"Unusual parameter type '{param.type}' in {endpoint.path} {method_name}"
                        )

                    # Check for custom formats
                    if param.format and param.format not in [
                        "pve-node",
                        "pve-vmid",
                        "pve-storage-id",
                        "email",
                        "uuid",
                    ]:
                        edge_cases.append(
                            f"Unknown format '{param.format}' in {endpoint.path} {method_name}"
                        )

            for child in endpoint.children:
                check_endpoint(child)

        for endpoint in endpoints:
            check_endpoint(endpoint)

        return edge_cases

    def _analyze_parameter_patterns(self, endpoints: List[Endpoint]) -> Dict[str, Any]:
        """Analyze parameter usage patterns across the schema.

        Args:
            endpoints: List of parsed Endpoint objects.

        Returns:
            Dictionary with parameter pattern analysis.
        """
        patterns = {
            "common_names": Counter(),
            "common_types": Counter(),
            "optional_ratios": {},
            "constraint_usage": Counter(),
        }

        def collect_patterns(endpoint: Endpoint):
            for method in endpoint.methods.values():
                for param in method.parameters:
                    patterns["common_names"][param.name] += 1
                    patterns["common_types"][param.type] += 1

                    # Track constraints
                    constraints = []
                    if param.minimum is not None or param.maximum is not None:
                        constraints.append("range")
                    if param.pattern:
                        constraints.append("pattern")
                    if param.enum:
                        constraints.append("enum")
                    if param.max_length:
                        constraints.append("length")
                    if param.format:
                        constraints.append("format")

                    for constraint in constraints:
                        patterns["constraint_usage"][constraint] += 1

            for child in endpoint.children:
                collect_patterns(child)

        for endpoint in endpoints:
            collect_patterns(endpoint)

        # Calculate optional ratios
        total_params = sum(patterns["common_names"].values())
        optional_count = 0

        def count_optional(endpoint: Endpoint):
            nonlocal optional_count
            for method in endpoint.methods.values():
                for param in method.parameters:
                    if param.optional:
                        optional_count += 1
            for child in endpoint.children:
                count_optional(child)

        for endpoint in endpoints:
            count_optional(endpoint)

        patterns["optional_ratios"] = {
            "optional": optional_count,
            "required": total_params - optional_count,
            "ratio": optional_count / total_params if total_params > 0 else 0,
        }

        return patterns

    def print_report(self, analysis: SchemaAnalysis) -> None:
        """Print a human-readable analysis report.

        Args:
            analysis: SchemaAnalysis to print.
        """
        print("=== Proxmox API Schema Analysis Report ===\n")

        print("STATISTICS:")
        print(f"  Total Endpoints: {analysis.stats.total_endpoints}")
        print(f"  Total Methods: {analysis.stats.total_methods}")
        print(f"  Total Parameters: {analysis.stats.total_parameters}")
        print(f"  Endpoints with Children: {analysis.stats.endpoints_with_children}")
        print(f"  Leaf Endpoints: {analysis.stats.leaf_endpoints}")
        print(f"  Endpoints with Path Params: {analysis.stats.endpoints_with_path_params}")
        print(f"  Unique Path Param Names: {sorted(analysis.stats.unique_path_param_names)}")
        print()

        print("METHOD COUNTS:")
        for method, count in sorted(analysis.stats.method_counts.items()):
            print(f"  {method}: {count}")
        print()

        print("PARAMETER TYPES:")
        for ptype, count in sorted(analysis.stats.parameter_type_counts.items()):
            print(f"  {ptype}: {count}")
        print()

        if analysis.stats.format_counts:
            print("CUSTOM FORMATS:")
            for fmt, count in sorted(analysis.stats.format_counts.items()):
                print(f"  {fmt}: {count}")
            print()

        print("PARAMETER PATTERNS:")
        print(f"  Optional Ratio: {analysis.parameter_patterns['optional_ratios']['ratio']:.2%}")
        print(f"  Most Common Names: {analysis.parameter_patterns['common_names'].most_common(5)}")
        print(f"  Most Common Types: {analysis.parameter_patterns['common_types'].most_common(5)}")
        print(f"  Constraint Usage: {dict(analysis.parameter_patterns['constraint_usage'])}")
        print()

        if analysis.edge_cases:
            print("EDGE CASES DETECTED:")
            for case in analysis.edge_cases:
                print(f"  - {case}")
            print()

        if analysis.common_models:
            print("POTENTIAL COMMON MODELS:")
            for name, params in analysis.common_models.items():
                print(f"  {name}: {len(params)} parameters")
            print()
