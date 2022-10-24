import ast
import operator
from typing import Any, Dict


class FormulaError(Exception):
    pass


class FormulaRuntimeError(FormulaError):
    pass


class FormulaSyntaxError(FormulaError):
    def __init__(self, msg: str, lineno: int, offset: int):
        self.msg = msg
        self.lineno = lineno
        self.offset = offset

    def __str__(self) -> str:
        return f"{self.lineno}:{self.offset}: {self.msg}"

    @staticmethod
    def byte_offset_to_char_offset(source: str, byte_offset: int) -> int:
        while True:
            try:
                pre_source = source.encode()[:byte_offset].decode()
                break
            except UnicodeDecodeError:
                byte_offset -= 1
                continue
        return len(pre_source)

    @classmethod
    def from_ast_node(
        cls, source: str, node: ast.AST, msg: str
    ) -> "FormulaSyntaxError":
        lineno = node.lineno
        col_offset = node.col_offset
        offset = cls.byte_offset_to_char_offset(source, col_offset)
        return cls(msg=msg, lineno=lineno, offset=offset + 1)

    @classmethod
    def from_syntax_error(cls, error: SyntaxError, msg: str) -> "FormulaSyntaxError":
        return cls(
            msg=f"{msg}: {error.msg}",
            lineno=error.lineno,
            offset=error.offset
        )


MAX_FORMULA_LENGTH = 255


def evaluate(formula: str, variables: Dict[str, Any]) -> float:
    if len(formula) > MAX_FORMULA_LENGTH:
        raise FormulaSyntaxError("The formula is too long", 1, 1)

    try:
        node = ast.parse(formula, "<string>", mode="eval")
    except SyntaxError as error:
        raise FormulaSyntaxError.from_syntax_error(error, "Could not parse") from error

    try:
        return eval_node(formula, node, variables)
    except FormulaSyntaxError:
        raise
    except Exception as error:
        raise FormulaRuntimeError(f"Evaluation failed: {error}") from error


def eval_node(source: str, node: ast.AST, variables: Dict[str, Any]) -> float:
    EVALUATORS = {
        ast.Expression: eval_expression,
        ast.Constant: eval_constant,
        ast.Name: eval_name,
        ast.BinOp: eval_binop,
        ast.UnaryOp: eval_unaryop,
    }

    for ast_type, evaluator in EVALUATORS.items():
        if isinstance(node, ast_type):
            return evaluator(source, node, variables)

    raise FormulaSyntaxError.from_ast_node(source, node, "This syntax is not supported")


def eval_expression(
    source: str, node: ast.Expression, variables: Dict[str, Any]
) -> float:
    return eval_node(source, node.body, variables)


def eval_constant(source: str, node: ast.Constant, variables: Dict[str, Any]) -> float:
    if isinstance(node.value, (float, int)):
        return float(node.value)

    raise FormulaSyntaxError.from_ast_node(
        source, node, "Literals of this type are not supported"
    )


def eval_name(source: str, node: ast.Name, variables: Dict[str, Any]) -> float:
    name = variables.get(node.id, None)  # variables[node.id]
    if isinstance(name, (float, int)):
        return float(name)
    if name.all():
        return name

    raise FormulaSyntaxError.from_ast_node(
        source, node, f"Undefined variable: {node.id}"
    )


def eval_binop(source: str, node: ast.BinOp, variables: Dict[str, Any]) -> float:
    OPERATIONS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    left_value = eval_node(source, node.left, variables)
    right_value = eval_node(source, node.right, variables)
    apply = OPERATIONS.get(type(node.op), None)  # OPERATIONS[type(node.op)]

    if apply:
        return apply(left_value, right_value)

    raise FormulaSyntaxError.from_ast_node(
        source, node, "Operations of this type are not supported"
    )


def eval_unaryop(source: str, node: ast.UnaryOp, variables: Dict[str, Any]) -> float:
    OPERATIONS = {
        ast.USub: operator.neg,
    }

    operand_value = eval_node(source, node.operand, variables)
    apply = OPERATIONS.get(type(node.op), None)  # OPERATIONS[type(node.op)]

    if apply:
        return apply(operand_value)

    raise FormulaSyntaxError.from_ast_node(
        source, node, "Operations of this type are not supported"
    )


if __name__ == "__main__":

    TEST_CASES = [
        ("2", {}),
        ("2.0", {}),
        ("2e-1", {}),
        ("1 + 2 * (3.0 / 4.0)", {}),
        ("a * b / c", {"a": 1.0, "b": 3, "c": 91}),
        ("''", {}),
        ("1 ** 2", {}),
        ("1 // 2", {}),
        ("not 2", {}),
        ("und", {}),
        ("and and", {}),
        ("c(1)", {}),
        ("1/0", {}),
        ("0" * 256, {}),
        ("lambda a:" * 28, {}),
        (
            "(points - 100 * bans) / gamesPlayed",
            {"points": 1200, "bans": 3, "gamesPlayed": 23},
        ),
    ]

    for eq, var in TEST_CASES:
        try:
            result = evaluate(eq, var)
            print(eq, "=", result)
        except FormulaError as error:
            print(eq, "raises", type(error), str(error))

    try:
        eq = '23+(7-5+((99-56)*2)-7+21/(7+6)-2*3)**(5*3)'
        result = evaluate(eq, {})
        print(eq, "=", result)
        print(23+(7-5+((99-56)*2)-7+21/(7+6)-2*3)**(5*3))
    except FormulaError as error:
        print(eq, "raises", type(error), str(error))
