import ast

tree = ast.parse("25 * (17 + 3) - 8", mode="eval")

print(ast.dump(tree, indent=4))