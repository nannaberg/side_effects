def check_and_or(mses, index):
    x1 = "- og"
    x2 = "- eller"
    x3 = "-og"
    x4 = "-eller"
    # xx3 = "- "
    for mse in mses:
        if x1 in mse:
            print("{}: {} was in {}".format(index, x1, mse))
        if x2 in mse:
            print("{}: {} was in {}".format(index, x2, mse))
        if x3 in mse:
            print("{}: {} was in {}".format(index, x3, mse))
        if x4 in mse:
            print("{}: {} was in {}".format(index, x4, mse))


def check_weird_comma_splits(mses, index):
    for mse in mses:
        if len(mse) > 0 and mse[0].islower():
            print("{}: WEIRD COMMA SPLIT ALERT -> {}".format(index, mse))


def check_weird_slash_cases(mses, index):
    x1 = "/"
    for mse in mses:
        if x1 in mse:
            print("{}: SLASH CASE -> {}".format(index, mse))


def check_weird_parentheses_cases(mses, index):
    x1 = "("
    x2 = ")"
    for mse in mses:
        if mse.count(x1) > 1 or mse.count(x2) > 1 or mse.count(x1) != mse.count(x2):
            # if x1 in mse or x2 in mse:
            print("{}: WEIRD PARENTHESIS CASE -> {}".format(index, mse))
