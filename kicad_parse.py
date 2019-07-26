from pyparsing import OneOrMore, nestedExpr, Dict


def list_to_dict(data: list) -> dict:
    """

    :param data:
    :return:
    """
    res = {}
    if not data or len(data) < 2:
        return res
    if len(data) == 2:
        res[data[0]] = data[1]
    else:
        res[data[0]] = data[1:]
    current_data = res[data[0]]
    if isinstance(current_data, list):
        for word in current_data:
            if isinstance(word, list):
                i = current_data.index(word)
                current_data[i] = list_to_dict(word)

    return res

if __name__ == '__main__':
    inputdata = open("FireFly.kicad_pcb").read()
    data = OneOrMore(nestedExpr()).parseString(inputdata)
    data = data.asList()
    a = list_to_dict(data[0])
    print(a)
    pass

