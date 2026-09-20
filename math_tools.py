import ast
import math
import operator


# ==========================
# 允许使用的数学运算
# ==========================

ALLOWED_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


# ==========================
# 允许使用的数学函数
# ==========================

ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "degrees": math.degrees,
    "radians": math.radians,
    "abs": abs,
    "round": round,
}


# ==========================
# 允许使用的数学常数
# ==========================

ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def check_number(value):

    if not isinstance(value, (int, float)):
        raise ValueError("结果不是普通数字")

    if not math.isfinite(float(value)):
        raise ValueError("结果不是有限数")

    if abs(value) > 1e100:
        raise ValueError("数字过大")

    return value


def evaluate_node(node):

    # 普通数字
    if isinstance(node, ast.Constant):

        if type(node.value) not in (int, float):
            raise ValueError("只允许数字")

        return check_number(node.value)


    # pi、e
    if isinstance(node, ast.Name):

        if node.id in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[node.id]

        raise ValueError(
            f"不允许使用变量：{node.id}"
        )


    # 二元运算
    if isinstance(node, ast.BinOp):

        operator_type = type(node.op)

        if operator_type not in ALLOWED_BINARY_OPERATORS:
            raise ValueError("不支持这个运算符")

        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        # 防止离谱的大指数
        if operator_type is ast.Pow and abs(right) > 100:
            raise ValueError("指数过大")

        result = ALLOWED_BINARY_OPERATORS[
            operator_type
        ](left, right)

        return check_number(result)


    # +x / -x
    if isinstance(node, ast.UnaryOp):

        operator_type = type(node.op)

        if operator_type not in ALLOWED_UNARY_OPERATORS:
            raise ValueError("不支持这个一元运算")

        value = evaluate_node(node.operand)

        return check_number(
            ALLOWED_UNARY_OPERATORS[
                operator_type
            ](value)
        )


    # sqrt()、sin() 等函数
    if isinstance(node, ast.Call):

        if not isinstance(node.func, ast.Name):
            raise ValueError("不允许这种函数调用")

        function_name = node.func.id

        if function_name not in ALLOWED_FUNCTIONS:
            raise ValueError(
                f"不允许调用函数：{function_name}"
            )

        if node.keywords:
            raise ValueError("不允许关键字参数")

        arguments = [
            evaluate_node(arg)
            for arg in node.args
        ]

        result = ALLOWED_FUNCTIONS[
            function_name
        ](*arguments)

        return check_number(result)


    raise ValueError("表达式包含不允许的内容")


# ==========================
# 高级数学计算器
# ==========================

def math_calculator(expression):

    try:

        expression = expression.strip()

        # 很多人习惯 ^ 表示幂
        expression = expression.replace("^", "**")

        if len(expression) > 300:
            raise ValueError("表达式过长")

        tree = ast.parse(
            expression,
            mode="eval"
        )

        result = evaluate_node(tree.body)

        return {
            "expression": expression,
            "result": result
        }

    except Exception as error:

        return {
            "expression": expression,
            "error": str(error)
        }
def track_stagger(
    lane,
    arc_fraction=1.0,
    lane_width=1.22,
    curb_radius=36.5,
    lane1_measure_offset=0.30,
    outer_lane_measure_offset=0.20
):

    lane = int(lane)

    if lane < 1:
        raise ValueError("道次必须大于等于1")


    # 第一跑道计量线半径
    lane1_radius = (
        curb_radius
        + lane1_measure_offset
    )


    # 当前跑道计量线半径
    if lane == 1:

        lane_radius = lane1_radius

    else:

        lane_radius = (
            curb_radius
            + (lane - 1) * lane_width
            + outer_lane_measure_offset
        )

    # 当前跑道与第一道之间的半径差
    radius_difference = (
        lane_radius
        - lane1_radius
    )


    # 两个半圆合起来相当于一个完整圆
    stagger_distance = (
        2
        * math.pi
        * radius_difference
        * arc_fraction
    )


    return {
        "lane": lane,

        "lane1_measure_radius_m":
            lane1_radius,

        "lane_measure_radius_m":
            lane_radius,

        "radius_difference_m":
            radius_difference,

        "arc_fraction":
            arc_fraction,

        "stagger_distance_m":
            stagger_distance
    }


# ==========================
# 批量计算多个跑道
# ==========================

def track_stagger_batch(
    lanes,
    arc_fraction=1.0,
    lane_width=1.22,
    curb_radius=36.5,
    lane1_measure_offset=0.30,
    outer_lane_measure_offset=0.20
):

    results = []

    for lane in lanes:

        result = track_stagger(
            lane=lane,
            arc_fraction=arc_fraction,
            lane_width=lane_width,
            curb_radius=curb_radius,
            lane1_measure_offset=lane1_measure_offset,
            outer_lane_measure_offset=outer_lane_measure_offset
        )

        results.append(result)

    return results