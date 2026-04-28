import pandas as pd
import matplotlib.pyplot as plt
import re
import os

class ASTNode:
    def __init__(self, command_type, file=None, metric=None, group=None, chart_type=None):
        self.command_type = command_type
        self.file = file
        self.metric = metric
        self.group = group
        self.chart_type = chart_type

    def __repr__(self):
        return (
            f"ASTNode(command_type='{self.command_type}', "
            f"file='{self.file}', metric='{self.metric}', "
            f"group='{self.group}', chart_type='{self.chart_type}')"
        )

   
class BizLangParser:
    def normalize(self, command):
        synonyms = {
            "earnings": "profit",
            "income": "revenue",
            "cost": "expense",
            "costs": "expense"
        }

        words = command.split()
        new_words = []

        for word in words:
            if ".csv" in word:
                new_words.append(word)
            else:
                new_words.append(synonyms.get(word, word))

        return " ".join(new_words)

    def parse(self, command):
        command = self.normalize(command.lower().strip())

        command = re.sub(r"[!,;:?]", "", command)

        compute_pattern = r"load\s+(\w+\.csv)\s+and\s+compute\s+(revenue|expense|profit|profit margin)\s+by\s+(region|product|month|date)"
        chart_pattern = r"generate\s+(bar|line)\s+chart\s+comparing\s+(revenue|expense|profit|profit margin)\s+by\s+(region|product|month|date)"
        pivot_pattern = r"create\s+pivot\s+table\s+by\s+(region|product|month|date)\s+and\s+(revenue|expense|profit|profit margin)"
        load_pattern = r"load\s+(\w+\.csv)"

        if match := re.search(compute_pattern, command):
            return ASTNode("compute", file=match.group(1), metric=match.group(2), group=match.group(3))

        elif match := re.search(chart_pattern, command):
            return ASTNode("chart", chart_type=match.group(1), metric=match.group(2), group=match.group(3))

        elif match := re.search(pivot_pattern, command):
            return ASTNode("pivot", group=match.group(1), metric=match.group(2))

        elif match := re.search(load_pattern, command):
            return ASTNode("load", file=match.group(1))

        else:
            raise SyntaxError("Invalid BizLang command. Please check grammar.")

class BizLangExecutor:
    def __init__(self):
        self.data = None

    def load_data(self, file):
        self.data = pd.read_csv(file)
        self.data["date"] = pd.to_datetime(self.data["date"])
        self.data["month"] = self.data["date"].dt.month_name()
        self.data["profit margin"] = self.data["profit"] / self.data["revenue"]
        print(f"Loaded file: {file}")
        print(self.data.head())

    def execute(self, ast):
        if ast.command_type == "load":
            self.load_data(ast.file)

        elif ast.command_type == "compute":
            self.load_data(ast.file)
            result = self.data.groupby(ast.group)[ast.metric].sum()
            print("\nComputed Result:")
            print(result)
            return result

        elif ast.command_type == "chart":
            if self.data is None:
                self.load_data("sales.csv")

            result = self.data.groupby(ast.group)[ast.metric].sum()

            if ast.chart_type == "bar":
                result.plot(kind="bar", title=f"{ast.metric.title()} by {ast.group.title()}")
            elif ast.chart_type == "line":
                result.plot(kind="line", marker="o", title=f"{ast.metric.title()} by {ast.group.title()}")

            plt.xlabel(ast.group.title())
            plt.ylabel(ast.metric.title())
            plt.tight_layout()
            plt.savefig("chart_output.png")
            plt.show()
            print("Chart saved as chart_output.png")

        elif ast.command_type == "pivot":
            if self.data is None:
                self.load_data("sales.csv")

            pivot = pd.pivot_table(
                self.data,
                values=ast.metric,
                index=ast.group,
                aggfunc="sum"
            )
            print("\nPivot Table:")
            print(pivot)
            return pivot


def show_parse_tree(command):
    print("\nParse Tree:")
    print("command")
    print(" ├── action")
    print(" ├── object")
    print(" ├── metric")
    print(" └── group/category")


def main():
    parser = BizLangParser()
    executor = BizLangExecutor()

    print("Welcome to BizLang: Business Analytics DSL")
    print("Example: Load sales.csv and compute revenue by region.")
    print("Type 'exit' to quit.\n")

    while True:
        command = input("BizLang> ")

        if command.lower() == "exit":
            break

        try:
            ast = parser.parse(command)
            print("\nAST:")
            print(ast)

            show_parse_tree(command)

            print("\nExecution Output:")
            executor.execute(ast)

        except Exception as e:
            print("Error:", e)
            print("\nSelf-Correction Suggestions:")

            print("1. Load sales.csv and compute revenue by region")
            print("2. Generate bar chart comparing revenue by region")
            print("3. Create pivot table by product and profit")
            print("4. Load sales.csv and compute earnings by region")

            if "compute" not in command.lower():
                print("Suggestion: Try 'Load sales.csv and compute revenue by region'")
            elif "chart" not in command.lower():
                print("Suggestion: Try 'Generate bar chart comparing revenue by region'")

if __name__ == "__main__":
    main()