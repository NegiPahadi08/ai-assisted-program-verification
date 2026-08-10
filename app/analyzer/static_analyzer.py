from __future__ import annotations

import ast
import builtins

from app.models.report import VerificationReport


class StaticAnalyzer(ast.NodeVisitor):
    """
    Performs deterministic static analysis using Python's AST.

    The analyzer looks for common programming problems such as:

    - division by zero
    - possible division by zero
    - undefined variables
    - mutable default arguments
    - bare except statements
    - eval / exec usage
    - possible infinite loops
    """

    def __init__(self, report: VerificationReport) -> None:
        self.report = report

        # Each function gets its own local scope.
        self.scope_stack: list[set[str]] = [set()]

        # Python built-in names are considered valid names.
        self.builtin_names = set(dir(builtins))

    @property
    def current_scope(self) -> set[str]:
        return self.scope_stack[-1]

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self._visit_function(node)

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:

        # Detect mutable default arguments.
        defaults = [
            *node.args.defaults,
            *node.args.kw_defaults,
        ]

        for default in defaults:
            if isinstance(
                default,
                (ast.List, ast.Dict, ast.Set),
            ):
                self.report.add_issue(
                    severity="WARNING",
                    message=(
                        "Mutable default argument may retain "
                        "state between function calls."
                    ),
                    line=default.lineno,
                    source="static",
                )

        # Collect function arguments.
        local_names = {
            argument.arg
            for argument in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
        }

        if node.args.vararg:
            local_names.add(node.args.vararg.arg)

        if node.args.kwarg:
            local_names.add(node.args.kwarg.arg)

        self.scope_stack.append(local_names)

        for statement in node.body:
            self.visit(statement)

        self.scope_stack.pop()

    def visit_Assign(
        self,
        node: ast.Assign,
    ) -> None:

        for target in node.targets:
            self._register_target(target)

        self.generic_visit(node)

    def visit_AnnAssign(
        self,
        node: ast.AnnAssign,
    ) -> None:

        self._register_target(node.target)

        self.generic_visit(node)

    def visit_AugAssign(
        self,
        node: ast.AugAssign,
    ) -> None:

        if (
            isinstance(node.target, ast.Name)
            and node.target.id not in self.current_scope
        ):
            self.report.add_issue(
                severity="WARNING",
                message=(
                    f"Variable '{node.target.id}' may be "
                    "used before assignment."
                ),
                line=node.lineno,
                source="static",
            )

        self._register_target(node.target)

        self.generic_visit(node)

    def _register_target(
        self,
        target: ast.AST,
    ) -> None:

        if isinstance(target, ast.Name):
            self.current_scope.add(target.id)

        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self._register_target(item)

    def visit_Name(
        self,
        node: ast.Name,
    ) -> None:

        if isinstance(node.ctx, ast.Load):

            known = any(
                node.id in scope
                for scope in reversed(self.scope_stack)
            )

            if (
                not known
                and node.id not in self.builtin_names
            ):
                self.report.add_issue(
                    severity="WARNING",
                    message=(
                        f"Name '{node.id}' may be undefined."
                    ),
                    line=node.lineno,
                    source="static",
                )

    def visit_BinOp(
        self,
        node: ast.BinOp,
    ) -> None:

        if isinstance(
            node.op,
            (
                ast.Div,
                ast.FloorDiv,
                ast.Mod,
            ),
        ):

            denominator = node.right

            # Example:
            #
            # x / 0
            #
            if (
                isinstance(denominator, ast.Constant)
                and denominator.value == 0
            ):
                self.report.add_issue(
                    severity="ERROR",
                    message="Division/modulo by zero detected.",
                    line=node.lineno,
                    source="static",
                )

            # Example:
            #
            # x / y
            #
            elif isinstance(
                denominator,
                ast.Name,
            ):
                self.report.add_issue(
                    severity="WARNING",
                    message=(
                        "Possible division/modulo by zero "
                        f"using '{denominator.id}'."
                    ),
                    line=node.lineno,
                    source="static",
                )

        self.generic_visit(node)

    def visit_ExceptHandler(
        self,
        node: ast.ExceptHandler,
    ) -> None:

        if node.type is None:
            self.report.add_issue(
                severity="WARNING",
                message=(
                    "Bare 'except' catches every exception "
                    "and may hide defects."
                ),
                line=node.lineno,
                source="static",
            )

        self.generic_visit(node)

    def visit_Call(
        self,
        node: ast.Call,
    ) -> None:

        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec"}
        ):
            self.report.add_issue(
                severity="WARNING",
                message=(
                    f"Use of {node.func.id} can execute "
                    "arbitrary code."
                ),
                line=node.lineno,
                source="static",
            )

        self.generic_visit(node)

    def visit_While(
        self,
        node: ast.While,
    ) -> None:

        # Detect:
        #
        # while True:
        #     ...
        #
        # when no obvious exit exists.

        if (
            isinstance(node.test, ast.Constant)
            and node.test.value is True
        ):

            has_exit = any(
                isinstance(
                    item,
                    (
                        ast.Break,
                        ast.Return,
                        ast.Raise,
                    ),
                )
                for item in ast.walk(node)
            )

            if not has_exit:
                self.report.add_issue(
                    severity="WARNING",
                    message=(
                        "Potential infinite loop: "
                        "while True has no visible "
                        "break, return, or raise."
                    ),
                    line=node.lineno,
                    source="static",
                )

        self.generic_visit(node)


def analyze_file(
    filename: str,
) -> VerificationReport:

    report = VerificationReport(
        file=filename,
    )

    try:
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as file:
            source = file.read()

    except Exception as exc:
        report.add_issue(
            severity="ERROR",
            message=str(exc),
            source="static",
        )

        report.calculate_status()

        return report

    # Parse the Python source code.
    try:
        tree = ast.parse(
            source,
            filename=filename,
        )

    except SyntaxError as exc:
        report.add_issue(
            severity="ERROR",
            message=f"Syntax error: {exc.msg}",
            line=exc.lineno,
            source="static",
        )

        report.calculate_status()

        return report

    report.syntax_valid = True

    analyzer = StaticAnalyzer(report)

    analyzer.visit(tree)

    report.calculate_status()

    return report
